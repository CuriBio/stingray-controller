// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import actions from "./actions";
import getters from "./getters";
import mutations from "./mutations";
import { ENUMS } from "./enums";

const default_state = {
  x_time_index: 0, // milliseconds
  barcodes: {
    plate_barcode: {
      value: null,
      valid: false
    },
    stim_barcode: {
      value: null,
      valid: false
    }
  }
};

// adapted from https://itnext.io/eating-my-advice-efficiently-improving-on-understanding-and-using-nuxt-vuex-6d00769014a2
const state = () => JSON.parse(JSON.stringify(default_state));

export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters,
  ENUMS
};
