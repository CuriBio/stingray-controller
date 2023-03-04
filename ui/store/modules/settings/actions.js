// import { callAxiosGetFromVuex, callAxiosPostFromVuex } from "@/js-utils/axiosHelpers.js";

export default {
  async sendFirmwareUpdateConfirmation(_, updateAccepted) {
    const status = updateAccepted ? "accepted" : "declined";
    console.log(`User ${status} firmware update`); // allow-log

    // const url = `/firmwareUpdateConfirmation?updateAccepted=${updateAccepted}`;
    // return await callAxiosPostFromVuex(url);
  },
  async update_settings() {
    const { activeUserIndex, userAccounts } = this.state.settings;

    const { customerId, userPassword, userName } = userAccounts[activeUserIndex];

    const params = {
      customerId,
      userName,
      userPassword,
    };

    // TODO
  },
};
