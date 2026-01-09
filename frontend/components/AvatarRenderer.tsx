import { createSignal, onMount, onCleanup, Show, createEffect, Suspense } from "solid-js";
import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { MTLLoader } from "three/addons/loaders/MTLLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { TAARenderPass } from "three/addons/postprocessing/TAARenderPass.js";

import LazyImage from "./LazyImage";

function get(hash: string) {
  for (var i = 31, t = 0; t < 38; t++) i ^= hash[t].charCodeAt(0);
  return `https://t${(i % 8).toString()}.rbxcdn.com/${hash}`;
}

export default function AvatarRenderer(props: { userId: number; class?: string }) {
  let containerRef: HTMLDivElement | undefined;
  let renderer: THREE.WebGLRenderer;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let animationFrameId: number;
  let pivot: THREE.Group;

  const [data, setData] = createSignal<ThreeDAvatar | null>(null);
  const [loading, setLoading] = createSignal(true);
  const [rendered, setRendered] = createSignal(false);

  createEffect(async () => {
    try {
      if (!props.userId && loading()) return;
      setLoading(true);
      cleanup();

      // await new Promise((resolve) => setTimeout(resolve, 0));

      let d = null;
      while (!d) {
        d = await pywebview.api.user.get_user_3d_avatar(props.userId);
        if (!d) {
          console.warn("Retrying to fetch 3D avatar data...");
          await new Promise((resolve) => setTimeout(resolve, 1000)); // Retry after 1 second
        }
      }
      // console.log("Fetched 3D avatar data:", d);

      setData(d);

      if (data() && containerRef) {
        await initThree(data()!);
      }
    } catch (e) {
      console.error("Failed to fetch 3D avatar", e);
    } finally {
      setLoading(false);
    }
  });

  const cleanup = () => {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    setRendered(false);

    if (scene) {
      scene.traverse((obj: any) => {
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) {
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m: any) => m.dispose());
          } else {
            obj.material.dispose();
          }
        }
      });
      scene.clear();
    }

    if (renderer) {
      renderer.dispose();
      if (renderer.domElement) renderer.domElement.remove();
      renderer = undefined!;
    }
  };

  onCleanup(cleanup);

  const initThree = async (avatar: ThreeDAvatar) => {
    if (!containerRef) return;
    cleanup();

    // await new Promise((resolve) => setTimeout(resolve, 0));

    const width = containerRef.clientWidth;
    const height = containerRef.clientHeight;

    scene = new THREE.Scene();

    // Setup Camera
    camera = new THREE.PerspectiveCamera(avatar.camera.fov, 900 / 600, 0.1, 1000);
    camera.position.set(
      avatar.camera.position.x,
      avatar.camera.position.y - 2,
      avatar.camera.position.z
    );

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    const currentRenderer = renderer;
    renderer.setSize(900, 600);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    containerRef.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.enablePan = false;
    controls.enableZoom = false;
    controls.target.set(
      (avatar.aabb.min.x + avatar.aabb.max.x) / 2,
      (avatar.aabb.max.y + avatar.aabb.min.y) / 2 + 1,
      0
    );

    // Light
    const ambientLight = new THREE.AmbientLight(0xffffff, 1);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xffffff, 0xffffff, 1);
    hemiLight.position.set(0, 25, 0);
    scene.add(hemiLight);

    // Key Light - Warm, main source
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.5);
    keyLight.position.set(5, 10, 7);
    scene.add(keyLight);

    // Fill Light - Cool, fills shadows
    const fillLight = new THREE.DirectionalLight(0xffffff, 1);
    fillLight.position.set(-5, 2, 7);
    scene.add(fillLight);

    // Rim Light - Highlights edges
    const rimLight = new THREE.DirectionalLight(0xffffff, 2);
    rimLight.position.set(0, 5, -10);
    scene.add(rimLight);

    // Pivot for rotation
    pivot = new THREE.Group();
    scene.add(pivot);

    // Post-processing
    const composer = new EffectComposer(renderer);
    const renderPass = new RenderPass(scene, camera);
    composer.addPass(renderPass);

    const taaPass = new TAARenderPass(scene, camera);
    // taaPass.unbiased = false;
    taaPass.sampleLevel = 2;
    composer.addPass(taaPass);

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height),
      0.01, // strength
      0.5, // radius
      0.1 // threshold
    );
    composer.addPass(bloomPass);

    const outputPass = new OutputPass();
    composer.addPass(outputPass);

    // Loader
    await new Promise<void>((resolve) => {
      const manager = new THREE.LoadingManager();
      manager.setURLModifier((url) => {
        const id = url.split("com/")[1];
        return get(id);
      });

      manager.onLoad = () => resolve();

      const mtlLoader = new MTLLoader(manager);
      mtlLoader.load(
        avatar.mtl,
        (materials: any) => {
          if (renderer !== currentRenderer) return;
          materials.preload();
          for (const key in materials.materials) {
            materials.materials[key].transparent = true;
            materials.materials[key].alphaMap = null;
            materials.materials[key].shininess = 0;
            materials.materials[key].envMap = null;
          }

          const objLoader = new OBJLoader(manager);
          objLoader.setMaterials(materials);

          objLoader.load(
            avatar.obj,
            (object) => {
              if (renderer !== currentRenderer) return;

              manager.setURLModifier((url) => {
                const id = url.split("com/")[1];
                return get(id);
              });
              pivot.add(object);

              // Clone for second pass (Player mesh with torso color)
              const object2 = object.clone();
              const torsoMaterial = new THREE.MeshPhongMaterial({
                color: new THREE.Color("#" + avatar.bodyColors.torsoColor3),
              });

              // Apply material and filter
              const playerChildren = object2.children.filter((child) =>
                child.name.toLowerCase().includes("player")
              );
              object2.children = playerChildren;

              object2.traverse((child) => {
                if (child instanceof THREE.Mesh) {
                  child.material = torsoMaterial;
                }
              });

              pivot.add(object2);
            },
            undefined,
            (error: unknown) => console.error("Error loading OBJ:", error)
          );
        },
        undefined,
        (error: unknown) => console.error("Error loading MTL:", error)
      );
    });

    renderer.compile(scene, camera);
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      pivot.rotation.y += 0.001;
      controls.update();
      composer.render();
    };
    animate();
    setRendered(true);
  };

  return (
    <Show when={data()}>
      <div
        ref={containerRef}
        class={` ${rendered() ? "animate-[fadeIn_0.3s_ease-out_forwards] " : " "} ${props.class}`}
      />
    </Show>
  );
}
