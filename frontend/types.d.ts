declare module "*.css";
declare module "@fontsource/*" {}
declare module "@fontsource-variable/*" {}

type Game = {
  id: number;
  name: string;
  description: string;
  placeId: number;
  creator: {
    id: number;
    name: string;
    type: string;
  };
  thumbnailUrl: string[];
  iconUrl: string;
  price: number;
  allowedGearGenres: string[];
  allowedGearCategories: string[];
  isGenreEnforced: boolean;
  copyingAllowed: boolean;
  playCount: number;
  visits: number;
  maxPlayers: number;
  created: string;
  updated: string;
  studioAccessToApisAllowed: boolean;
  createVipServersAllowed: boolean;
  universeAvatarType: string;
  genre: string;
  isAllGenre: boolean;
  isFavoritedByUser: boolean;
  favoritedCount: number;
  upvotes: number;
  downvotes: number;
  playability: {
    isPlayable: boolean;
    playabilityStatus: string;
  };
};

type FriendT = {
  id: number;
  name: string;
  displayName: string;
  presence: {
    type: string;
    place: number | null;
    universe: number | null;
    job: number | null;
    lastLocation: string | null;
  };
  image: string;
  friendStatus?: "Friends" | "NotFriends" | "RequestSent" | "RequestReceived";
  imageBust?: string;
};

type Friend = FriendT & {
  followersCount: number;
  followingCount: number;
  friendCount: number;
  isFollowersFetched: boolean;
};

type Server = {
  id: string;
  maxPlayers: number;
  playing: number;
  playerTokens: Array<string>;
  playerAvatars: Array<string>;
  fps: number;
  ping: number;
  nextCursor: string;
};

type PrivateServer = Server & {
  name: string;
  accessCode: string;
  owner: {
    id: number;
    name: string;
    displayName: string;
  };
};

declare const pywebview: {
  api: {
    open_uri(uri: string): Promise<void>;
    auth: {
      login(): Promise<{
        id: number;
        name: string;
        displayName: string;
      }>;
      get_last_account(): Promise<{ id: number; name: string; displayName: string } | null>;
      purge_database(): Promise<void>;
      get_all_accounts(): Promise<
        Array<{ id: number; name: string; displayName: string; image: string }>
      >;
      switch_account(account_id: number): Promise<{
        id: number;
        name: string;
        displayName: string;
      }>;
      delete_account(account_id: number): Promise<void>;
      get_authentication_ticket(): Promise<string>;
    };
    user: {
      get_authed_user(): Promise<{
        id: number;
        name: string;
        displayName: string;
        robux: number;
        image: string;
      }>;

      get_followers_count(user_id: number): Promise<{
        followersCount: number;
        followingCount: number;
        friendCount: number;
      }>;

      search_users(query: string, page_size?: number): Promise<Array<FriendT>>;
    };
    friends: {
      get_authed_friends(iterate: [number, number]): Promise<Array<FriendT>>;
      send_friend_request(user_id: number): Promise<boolean>;
      remove_friend(user_id: number): Promise<boolean>;
      accept_friend_request(user_id: number): Promise<boolean>;
      decline_friend_request(user_id: number): Promise<boolean>;
    };
    games: {
      get_authed_recommendations(max_per_page?: number): Promise<Array<Game>>;
      get_authed_recommendations_page(page?: number): Promise<Array<Game>>;
      get_authed_continue(max_per_page?: number): Promise<Array<Game>>;
      get_authed_continue_page(page?: number): Promise<Array<Game>>;
      get_authed_favorites(max_per_page?: number): Promise<Array<Game>>;
      get_authed_favorites_page(page?: number): Promise<Array<Game>>;
      get_servers(place_id: number, page_size?: number): Promise<Array<Server>>;
      get_servers_next_page(): Promise<Array<Server>>;
      get_servers_private(place_id: number, page_size?: number): Promise<Array<>>;
      get_servers_private_next_page(): Promise<Array<PrivateServer>>;
      get_vote_status(universe_id: number): Promise<{
        canVote: boolean;
        userVote: boolean;
        reason: string | null;
      }>;
      set_vote(universe_id: number, upvote: boolean): Promise<void>;
      set_favorite(universe_id: number, favorite: boolean): Promise<void>;
      search_universes(query: string): Promise<[string, Array<Game>]>;
      search_universes_next_page(): Promise<[string, Array<Game>]>;
      search_suggestions(query: string): Promise<Array<string>>;
    };
    utility: {
      launch_roblox(
        launch_mode: "Play" | "Edit",
        ticket?: string,
        place_id?: number,
        follow_user_id?: number,
        job_id?: string,
        private_id?: string
      ): Promise<boolean>;
      launch_roblox_with_id(
        launch_mode: "Play" | "Edit",
        account_id: number,
        place_id?: number,
        follow_user_id?: number,
        job_id?: string,
        private_id?: string
      ): Promise<boolean>;
      create_shortcut(
        game_name: string,
        place_id: number,
        account_name: string,
        account_id: number,
        image_url: string
      ): Promise<boolean>;
    };
  };
};
