// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import actions from "./actions";
import getters from "./getters";
import mutations from "./mutations";
import { STATUS } from "./enums";

const defaultState = {
  port: 4567, // http://localhost:4567/
  statusUuid: STATUS.SERVER_INITIALIZING_STATE,
  simulationMode: false,
  barcodeManualMode: false,
  isConnectedToController: false,
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
  shutdownStatus: false,
  shutdownErrorMessage: "Stingray software is about to shut down.",
  shutdownErrorStatus: "",
  installerLink: null,
  softwareUpdateAvailable: false,
  firmwareUpdateAvailable: false,
  firmwareUpdateDurMins: null,
  allowSWUpdateInstall: false,
  confirmationRequest: false,
};

// adapted from https://itnext.io/eating-my-advice-efficiently-improving-on-understanding-and-using-nuxt-vuex-6d00769014a2
const state = () => JSON.parse(JSON.stringify(defaultState));

export default {
  namespaced: true,
  state,
  actions,
  mutations,
  getters,
  STATUS,
};
