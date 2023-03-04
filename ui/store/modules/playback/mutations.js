// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

export default {
  setBarcode(state, { type, newValue, isValid }) {
    state.barcodes[type].value = newValue;
    state.barcodes[type].valid = isValid;
  },
  setBarcodeWarning(state, bool) {
    state.barcodeWarning = bool;
  },
};
