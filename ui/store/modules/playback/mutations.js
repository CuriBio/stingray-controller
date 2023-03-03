// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

export default {
  setBarcode(state, { type, new_value, is_valid }) {
    state.barcodes[type].value = new_value;
    state.barcodes[type].valid = is_valid;
  },
  setBarcodeWarning(state, bool) {
    state.barcode_warning = bool;
  },
};
