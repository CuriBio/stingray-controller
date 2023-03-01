// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files
export default {
  set_plate_waveforms(state, new_value) {
    state.plate_waveforms = [...new_value];
  },
  clear_plate_waveforms(state) {
    for (let i = 0; i < state.plate_waveforms.length; i++) {
      state.plate_waveforms[i] = { x_data_points: [], y_data_points: [] };
    }
  },
  set_stim_waveforms(state, new_value) {
    state.stim_waveforms = new_value;
  },
  clear_stim_waveforms(state) {
    for (let i = 0; i < state.stim_waveforms.length; i++) {
      state.stim_waveforms[i] = { x_data_points: [], y_data_points: [] };
      state.stim_fill_assignments[i] = [];
      state.last_protocol_flag[i] = [];
    }
  },
  set_fill_colors(state, payload) {
    const { stim_fill_colors, well } = payload;
    const copy = state.stim_fill_colors; // required to be reactive
    copy[well] = stim_fill_colors;
    state.stim_fill_colors = { ...copy };
  },
  set_stimulator_circuit_statuses(state, stimulator_statuses) {
    state.stimulator_circuit_statuses = [...stimulator_statuses];
  },
  
  set_barcode(state, { type, new_value, is_valid }) {
    state.barcodes[type].value = new_value;
    state.barcodes[type].valid = is_valid;
  }
};
