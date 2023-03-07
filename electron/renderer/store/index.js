// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import Vuex from "vuex";
import {
  settings_store_module,
  system_store_module,
  socket,
  create_web_socket_plugin,
  stimulation_store_module,
} from "@curi-bio/ui";

const ws_plugin = create_web_socket_plugin(socket);

const createStore = () => {
  return new Vuex.Store({
    // namespaced: true, // this doesn't seem to do anything...(Eli 4/1/20) each module seems to need to be namespaced: true individually https://vuex.vuejs.org/guide/modules.html
    modules: {
      system: system_store_module,
      settings: settings_store_module,
      stimulation: stimulation_store_module,
    },
    plugins: [ws_plugin],
  });
};

export default createStore;
