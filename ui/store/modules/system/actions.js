import { STIM_STATUS } from "../stimulation/enums";
import { TextValidation } from "@/js-utils/TextValidation.js";
import { socket } from "@/store/plugins/websocket";

const TextValidationPlateBarcode = new TextValidation("plateBarcode");

export default {
  async validateBarcode({ commit, state }, { type, newValue }) {
    const result = TextValidationPlateBarcode.validate(newValue, type);
    const isValid = result == "";

    // stop all running processes if either barcode changes regardless of validity
    if (this.state.stimulation.stimPlayState) {
      await this.dispatch("stimulation/stopStimulation");
      commit("setBarcodeWarning", true);
    }
    // require new stim configuration check if either new barcode changes
    if (isValid && state.barcodes[type].value !== newValue) {
      this.commit("stimulation/setStimStatus", STIM_STATUS.CONFIG_CHECK_NEEDED);
    }

    commit("setBarcode", { type, newValue, isValid });
  },
  async sendFirmwareUpdateConfirmation(_, updateAccepted) {
    const status = updateAccepted ? "accepted" : "declined";
    console.log(`User ${status} firmware update`); // allow-log

    const wsMessage = JSON.stringify({
      command: "firmware_update_confirmation",
      update_accepted: updateAccepted,
    });

    socket.send(wsMessage);
  },
  async sendSetLatestSwVersion(_, latestSwVersionAvailable) {
    const wsMessage = JSON.stringify({
      command: "set_latest_software_version",
      version: latestSwVersionAvailable,
    });

    socket.send(wsMessage);
  },
};
