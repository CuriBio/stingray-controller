// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import Vuex from "vuex";
import {
  settingsStoreModule,
  systemStoreModule,
  socket,
  createWebSocketPlugin,
  stimulationStoreModule,
} from "@curi-bio/ui";

const wsPlugin = createWebSocketPlugin(socket);

const createStore = () => {
  return new Vuex.Store({
    // namespaced: true, // this doesn't seem to do anything...(Eli 4/1/20) each module seems to need to be namespaced: true individually https://vuex.vuejs.org/guide/modules.html
    modules: {
      system: systemStoreModule,
      settings: settingsStoreModule,
      stimulation: stimulationStoreModule,
    },
    plugins: [wsPlugin],
  });
};

export default createStore;
