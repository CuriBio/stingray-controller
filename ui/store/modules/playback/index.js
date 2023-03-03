// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import actions from "./actions";
import getters from "./getters";
import mutations from "./mutations";
import { ENUMS } from "./enums";

const defaultState = {
  xTimeIndex: 0, // milliseconds
  barcodes: {
    plateBarcode: {
      value: null,
      valid: false,
    },
    stimBarcode: {
      value: null,
      valid: false,
    },
  },
};

// adapted from https://itnext.io/eating-my-advice-efficiently-improving-on-understanding-and-using-nuxt-vuex-6d00769014a2
const state = () => JSON.parse(JSON.stringify(defaultState));

export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters,
  ENUMS,
};
