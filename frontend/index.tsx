/* @refresh reload */
import { render } from "solid-js/web";
import App from "./App.tsx";
import "@fontsource-variable/rubik";

const root = document.getElementById("root");

render(() => <App />, root!);

