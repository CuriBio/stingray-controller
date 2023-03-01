// import { call_axios_get_from_vuex, call_axios_post_from_vuex } from "@/js_utils/axios_helpers.js";

export default {
  async send_firmware_update_confirmation(_, update_accepted) {
    const status = update_accepted ? "accepted" : "declined";
    console.log(`User ${status} firmware update`); // allow-log

    // const url = `/firmware_update_confirmation?update_accepted=${update_accepted}`;
    // return await call_axios_post_from_vuex(url);
  },
};
