<template>
  <div>
    <div class="div__sidebar">
      <div class="div__sidebar-page-divider" />
      <div class="div__component-container">
        <div class="div__plate-barcode-container">
          <BarcodeViewer />
        </div>
        <div class="div__stim-barcode-container">
          <BarcodeViewer :barcodeType="'stimBarcode'" />
        </div>
        <div class="div__stim-status-container">
          <StatusBar :stimSpecific="true" @send-confirmation="sendConfirmation" />
        </div>
        <div class="div__stimulation-controls-icon-container">
          <StimulationStudioControls />
        </div>
        <div class="div__simulation-mode-container">
          <SimulationMode />
        </div>
        <span class="span__copyright"
          >&copy;{{ currentYear }} Curi Bio. All Rights Reserved. Version:
          {{ packageVersion }}
        </span>
      </div>
    </div>
    <div class="div__top-header-bar" />
    <div class="div__nuxt-page">
      <nuxt />
    </div>
  </div>
</template>
<script>
import Vue from "vue";

import { BarcodeViewer, StatusBar, SimulationMode, StimulationStudioControls } from "@curi-bio/ui";

import { ipcRenderer } from "electron";

import { mapState } from "vuex";
import { VBPopover, VBToggle } from "bootstrap-vue";

// Note: Vue automatically prefixes the directive name with 'v-'
Vue.directive("b-popover", VBPopover);
Vue.directive("b-toggle", VBToggle);

export default {
  components: {
    BarcodeViewer,
    StatusBar,
    SimulationMode,
    StimulationStudioControls,
  },
  data: function () {
    return {
      packageVersion: "",
      latestSwVersionAvailable: null,
      currentYear: "2023", // TODO look into better ways of handling this. Not sure if just using the system's current year is the best approach
    };
  },
  computed: {
    ...mapState("stimulation", ["stimPlayState"]),
    ...mapState("system", ["statusUuid", "allowSWUpdateInstall", "isConnectedToController"]),
  },
  watch: {
    allowSwUpdateInstall: function () {
      ipcRenderer.send("set_sw_update_auto_install", this.allowSWUpdateInstall);
    },
    latestSwVersionAvailable: function () {
      this.setLatestSwVersion();
    },
    isConnectedToController: function () {
      this.setLatestSwVersion();
    },
  },
  created: async function () {
    // ipcRenderer.on("logs_flask_dir_response", (e, log_dir_name) => {
    //   this.$store.commit("settings/set_log_path", log_dir_name);
    //   this.log_dir_name = log_dir_name;
    //   const filename_prefix = path.basename(log_dir_name);

    //   // Only way to create a custom file path for the renderer process logs
    //   log.transports.file.resolvePath = () => {
    //     const filename = filename_prefix + "_renderer.txt";
    //     return path.join(this.log_dir_name, filename);
    //   };
    //   // set to UTC, not local time
    //   process.env.TZ = "UTC";
    //   console.log = log.log;
    //   console.error = log.error;
    //   console.log("Initial view has been rendered"); // allow-log
    // });

    // if (this.log_dir_name === undefined) {
    //   ipcRenderer.send("logs_flask_dir_request");
    // }

    // TODO make all these event names camelCase

    // the version of the running (current) software is stored in the main process of electron, so request it to be sent over to this process
    ipcRenderer.on("sw_version_response", (_, packageVersion) => {
      this.packageVersion = packageVersion;
    });
    if (this.packageVersion === "") {
      ipcRenderer.send("sw_version_request");
    }

    // the electron auto-updater runs in the main process of electron, so request it to be sent over to this process
    ipcRenderer.on("latest_sw_version_response", (_, latestSwVersionAvailable) => {
      this.latestSwVersionAvailable = latestSwVersionAvailable;
    });
    if (this.latestSwVersionAvailable === null) {
      ipcRenderer.send("latest_sw_version_request");
    }

    // TODO
    // ipcRenderer.on("confirmation_request", () => {
    //   this.$store.commit("settings/setConfirmationRequest", true);
    // });

    // TODO ?
    // ipcRenderer.on("stored_accounts_response", (_, stored_accounts) => {
    //   // stored_accounts will contain both customer_id and usernames
    //   this.request_stored_accounts = false;
    //   this.stored_accounts = stored_accounts;
    //   this.$store.commit("settings/set_stored_accounts", stored_accounts);
    // });
    // if (this.request_stored_accounts) {
    //   ipcRenderer.send("stored_accounts_request");
    // }
  },
  methods: {
    sendConfirmation: function () {
      this.$store.commit("settings/setConfirmationRequest", false);
    },
    setLatestSwVersion: function () {
      if (this.latestSwVersionAvailable && this.isConnectedToController) {
        this.$store.dispatch("system/sendSetLatestSwVersion", this.latestSwVersionAvailable);
      }
    },
  },
};
</script>

<style type="text/css">
body {
  background-color: #000000;
}

.div__nuxt-page {
  position: absolute;
  top: 0px;
  left: 289px;
}

/* ACCORDIAN*/
.div__component-container {
  top: 45px;
  position: absolute;
  width: 287px;
}

/* NON-SPECIFIC */
.div__top-header-bar {
  position: absolute;
  left: 289px;
  background-color: #111111;
  height: 45px;
  width: 1629px;
}

.div__sidebar {
  background-color: #1c1c1c;
  position: absolute;
  top: 0px;
  left: 0px;
  height: 930px;
  width: 287px;
}

.div__sidebar-page-divider {
  position: absolute;
  top: 0px;
  left: 287px;
  width: 2px;
  height: 930px;
  background-color: #0e0e0e;
}

/* DATA-ACQUISITION */
.div__plate-barcode-container {
  position: relative;
  left: 0px;
}

/* STIM STUDIO */
.div__stim-status-container {
  position: relative;
  margin-top: 8px;
}

.div__stim-barcode-container {
  position: relative;
  left: 0px;
  margin-top: 10px;
}

.div__stimulation-controls-icon-container {
  position: relative;
  margin-top: 3px;
  left: 0px;
  overflow: hidden;
}

/* STIMULATION/COPYRIGHT */
.div__simulation-mode-container {
  position: absolute;
  top: 875px;
}

.span__copyright {
  position: absolute;
  z-index: 99;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
  box-sizing: border-box;
  line-height: 100%;
  overflow: hidden;
  width: 286px;
  height: 16px;
  top: 907px;
  left: -0.252101px;
  padding: 5px;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 9px;
  color: #ffffff;
  text-align: center;
}
</style>
