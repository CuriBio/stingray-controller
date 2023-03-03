// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import Vuex from "vuex";
import flaskModule from "./modules/flask";
import settingsModule from "./modules/settings";
import stimulationModule from "./modules/stimulation";
import playbackModule from "./modules/playback";
import { default as createWebSocketPlugin, socket } from "./plugins/websocket";

// const wsPlugin = createWebSocketPlugin(socket);

const createStore = () => {
  return new Vuex.Store({
    // namespaced: true, // this doesn't seem to do anything...(Eli 4/1/20) each module seems to need to be namespaced: true individually https://vuex.vuejs.org/guide/modules.html
    modules: {
      flask: flaskModule,
      stimulation: stimulationModule,
      settings: settingsModule,
      playback: playbackModule,
    },
    // plugins: [wsPlugin],
  });
};

export default createStore;
