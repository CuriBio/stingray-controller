// adapted from https://stackoverflow.com/questions/53446792/nuxt-vuex-how-do-i-break-down-a-vuex-module-into-separate-files

import { ENUMS } from "./enums";
import { STIM_STATUS } from "../stimulation/enums";
import { TextValidation } from "@/js_utils/text_validation.js";
const TextValidation_plate_barcode = new TextValidation("plate_barcode");
// =========================================================================
// |   Following are the list of items called --todo                       |
// |   a) baseurl {contains the flask server url } {obtain from config.ini}|
// |   b) api's /start_managed_acquisition         {obtain from config.ini}|
// |            /stop_managed_acquisition                                  |
// |            /start_recording                                           |
// |            /stop_recording                                            |
// |            /start_calibration                                         |
// |                                                                       |
// |  NOTE: The python flask server as development can manage api's by     |
// |        version eg:- /v{n}/start_managed_acquisition                   |
// |        in-order to have loose-coupling and App/UI changes can be      |
// |        rollout feature without Python Flask server change its good for|
// |        to have config.ini allowing App/UI to discover api's           |
// =========================================================================

export const micros_per_milli = 1000;
/**
 * Function to progress the time_index
 * @return {void}
 */
export function advance_playback_progression() {
  const delay_threshold_milliseconds = this.rootState.playback.num_milliseconds_to_fast_forward_if_delayed;
  const starting_timestamp = this.rootState.playback.timestamp_of_beginning_of_progression;
  const expected_display_time = starting_timestamp + this.rootState.playback.x_time_index / micros_per_milli;
  const current_timestamp = performance.now();
  let milliseconds_to_increment = this.rootState.playback.playback_progression_time_interval;
  if (current_timestamp - expected_display_time >= delay_threshold_milliseconds) {
    milliseconds_to_increment = delay_threshold_milliseconds;
  }
  this.commit("increment_x_time_index", milliseconds_to_increment * micros_per_milli);
}

export default {
  async get_playback_action_context(context) {
    // useful for testing actions
    return context;
  },


  async validate_barcode({ commit, state, dispatch }, { type, new_value }) {
    const result = TextValidation_plate_barcode.validate(new_value, type, this.state.settings.beta_2_mode);
    const is_valid = result == "";

    // stop all running processes if either barcode changes regardless of validity
    if (this.state.stimulation.stim_play_state) {
      await this.dispatch("stimulation/stop_stimulation");
      commit("set_barcode_warning", true);
    }

    if (state.playback_state === ENUMS.PLAYBACK_STATES.LIVE_VIEW_ACTIVE) {
      await dispatch("stop_live_view");
      commit("set_barcode_warning", true);
    } else if (state.playback_state === ENUMS.PLAYBACK_STATES.RECORDING) {
      await dispatch("stop_recording");
      await dispatch("stop_live_view");

      commit("set_barcode_warning", true);
    }

    // require new stim configuration check if either new barcode changes
    if (is_valid && state.barcodes[type].value !== new_value) {
      this.commit("stimulation/set_stim_status", STIM_STATUS.CONFIG_CHECK_NEEDED);
    }

    commit("set_barcode", { type, new_value, is_valid });
  },

};
