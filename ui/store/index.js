// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import Vuex from "vuex";
import systemModule from "./modules/system";
import settingsModule from "./modules/settings";
import stimulationModule from "./modules/stimulation";

const createStore = () => {
  return new Vuex.Store({
    // namespaced: true, // this doesn't seem to do anything...(Eli 4/1/20) each module seems to need to be namespaced: true individually https://vuex.vuejs.org/guide/modules.html
    modules: {
      system: systemModule,
      stimulation: stimulationModule,
      settings: settingsModule,
    },
  });
};

export default createStore;
