// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import Vuex from "vuex";
import data_module from "./modules/data";
import flask_module from "./modules/flask";
import settings_module from "./modules/settings";
import stimulation_module from "./modules/stimulation";
import playback_module from "./modules/playback";
import { default as create_web_socket_plugin, socket } from "./plugins/websocket";

const ws_plugin = create_web_socket_plugin(socket);

const createStore = () => {
  return new Vuex.Store({
    // namespaced: true, // this doesn't seem to do anything...(Eli 4/1/20) each module seems to need to be namespaced: true individually https://vuex.vuejs.org/guide/modules.html
    modules: {
      data: data_module,
      flask: flask_module,
      stimulation: stimulation_module,
      settings: settings_module,
      playback: playback_module
    },
    plugins: [ws_plugin]
  });
};

export default createStore;
