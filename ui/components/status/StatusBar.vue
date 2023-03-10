<template>
  <div class="div__status-bar">
    <span class="span__status-bar-text">Status: {{ alertTxt }}</span>
    <span>
      <b-modal id="error-catch" size="sm" hide-footer hide-header hide-header-close :static="true">
        <ErrorCatchWidget :logFilepath="logPath" @ok-clicked="closeModalsById(['error-catch'])" />
      </b-modal>
      <b-modal
        id="fw-updates-complete-message"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget
          :modalLabels="fwUpdatesCompleteLabels"
          @handle-confirmation="closeModalsById(['fw-updates-complete-message'])"
        />
      </b-modal>
      <b-modal
        id="short-circuit-err"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget
          :modalLabels="shortCircuitLabels"
          :emailError="true"
          @handle-confirmation="closeModalsById(['short-circuit-err'])"
        />
      </b-modal>
      <b-modal
        id="fw-updates-in-progress-message"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusSpinnerWidget :modalLabels="fwUpdateInProgressLabels" />
      </b-modal>
      <b-modal
        id="sw-update-message"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget :modalLabels="swUpdateLabels" @handle-confirmation="closeSwUpdateModal" />
      </b-modal>
      <b-modal
        id="fw-closure-warning"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget
          :modalLabels="fwClosureWarningLabels"
          @handle-confirmation="handleConfirmation"
        />
      </b-modal>
      <b-modal
        id="ops-closure-warning"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget @handle-confirmation="handleConfirmation" />
      </b-modal>
      <b-modal
        id="failed-qc-check"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StimQCSummary @handle-confirmation="closeModalsById(['failed-qc-check'])" />
      </b-modal>
      <b-modal
        id="success-qc-check"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget
          :modalLabels="successfulQcCheckLabels"
          @handle-confirmation="closeModalsById(['success-qc-check'])"
        />
      </b-modal>
    </span>
  </div>
</template>
<script>
import Vue from "vue";
import { mapGetters, mapState } from "vuex";
import { STATUS } from "@/store/modules/system/enums";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import BootstrapVue from "bootstrap-vue";
import { BButton } from "bootstrap-vue";
import { BModal } from "bootstrap-vue";
import ErrorCatchWidget from "@/components/status/ErrorCatchWidget.vue";
import StatusWarningWidget from "@/components/status/StatusWarningWidget.vue";
import StatusSpinnerWidget from "@/components/status/StatusSpinnerWidget.vue";
import StimQCSummary from "@/components/status/StimQCSummary.vue";

Vue.use(BootstrapVue);
Vue.component("BButton", BButton);
Vue.component("BModal", BModal);

export default {
  name: "StatusBar",
  components: {
    ErrorCatchWidget,
    StatusWarningWidget,
    StatusSpinnerWidget,
    StimQCSummary,
  },
  data() {
    return {
      alertTxt: "",
      fwClosureWarningLabels: {
        header: "Warning!",
        msgOne:
          "A firmware update for the Stingray instrument is in progress. Closing the software now could damage the instrument.",
        msgTwo: "Are you sure you want to exit?",
        buttonNames: ["Cancel", "Yes"],
      },
      fwUpdatesCompleteLabels: {
        header: "Important!",
        msgOne: "Firmware updates have been successfully installed.",
        msgTwo:
          "Please close the Stingray software, power the Stingray instrument off and on, then restart the Stingray software.",
        buttonNames: ["Okay"],
      },
      swUpdateLabels: {
        header: "Important!",
        msgOne: "A software update will be installed after exiting.",
        msgTwo:
          "The installer may prompt you to take action while it is running. Please watch it after this software closes.",
        buttonNames: ["Okay"],
      },
      shortCircuitLabels: {
        header: "Error!",
        msgOne: "A short circuit has been found during the configuration check. Replace the stimulation lid.",
        msgTwo: "If the issue persists, please contact:  ",
        buttonNames: ["Okay"],
      },
      successfulQcCheckLabels: {
        header: "Configuration Check Complete!",
        msgOne: "No open circuits were detected in a well assigned with a protocol.",
        msgTwo: "You can now run this stimulation.",
        buttonNames: ["Okay"],
      },
    };
  },
  computed: {
    ...mapGetters({
      statusUuid: "system/statusId",
    }),
    ...mapState("stimulation", [
      "stimulatorCircuitStatuses",
      "protocolAssignments",
      "stimPlayState",
      "stimStatus",
    ]),
    ...mapState("settings", ["logPath"]),
    ...mapState("system", [
      "shutdownErrorStatus",
      "softwareUpdateAvailable",
      "allowSWUpdateInstall",
      "firmwareUpdateDurMins",
      "confirmationRequest",
      "statusUuid",
    ]),
    fwUpdateInProgressLabels: function () {
      let duration = `${this.firmwareUpdateDurMins} minute`;
      if (this.firmwareUpdateDurMins !== 1) duration += "s";
      return {
        header: "Important!",
        msgOne: `The firmware update is in progress. It will take about ${duration} to complete.`,
        msgTwo: "Do not close the Stingray software or power off the Stingray instrument.",
      };
    },

    assignedOpenCircuits: function () {
      // filter for matching indices
      return this.stimulatorCircuitStatuses.filter((well) =>
        Object.keys(this.protocolAssignments).includes(well.toString())
      );
    },
    isInitializing: function () {
      return [
        STATUS.SERVER_INITIALIZING_STATE,
        STATUS.SERVER_READY_STATE,
        STATUS.INSTRUMENT_INITIALIZING_STATE,
      ].includes(this.statusUuid);
    },
    isUpdating: function () {
      return [
        STATUS.CHECKING_FOR_UPDATES_STATE,
        STATUS.INSTALLING_UPDATES_STATE,
        STATUS.DOWNLOADING_UPDATES_STATE,
      ].includes(this.statusUuid);
    },
  },
  watch: {
    statusUuid: function (newStatus) {
      // set message for stimulation status and system status if error occurs
      if (!this.shutdownErrorStatus && newStatus !== STATUS.IDLE_READY_STATE)
        this.setSystemSpecificStatus(newStatus);
      else if (newStatus === STATUS.IDLE_READY_STATE) this.setStimSpecificStatus();
    },
    stimStatus: function (newStatus) {
      // only let stim messages through if system is in idle ready state
      if (this.statusUuid === STATUS.IDLE_READY_STATE) this.setStimSpecificStatus(newStatus);
    },
    confirmationRequest: function () {
      const stimOpsInProgress =
        this.stimStatus === STIM_STATUS.CONFIG_CHECK_IN_PROGRESS || this.stimPlayState;

      const fwUpdateInProgress =
        this.statusUuid === STATUS.DOWNLOADING_UPDATES_STATE ||
        this.statusUuid === STATUS.INSTALLING_UPDATES_STATE;

      if (this.confirmationRequest) {
        if (fwUpdateInProgress) {
          this.$bvModal.show("fw-closure-warning");
        } else if (stimOpsInProgress) {
          this.$bvModal.show("ops-closure-warning");
        } else {
          this.handleConfirmation(1);
        }
      }
    },
    shutdownErrorStatus: function (newVal, _) {
      if (newVal) {
        this.closeModalsById(["fw-updates-in-progress-message", "fw-closure-warning", "ops-closure-warning"]);
        this.alertTxt = "Error Occurred";
        this.$bvModal.show("error-catch");
      }
    },
  },
  created() {
    this.setSystemSpecificStatus(this.statusUuid);
  },
  methods: {
    setStimSpecificStatus: function (status) {
      this.alertTxt = status ? status : this.stimStatus;

      if (status === STIM_STATUS.CONFIG_CHECK_COMPLETE)
        this.assignedOpenCircuits.length > 0
          ? this.$bvModal.show("failed-qc-check")
          : this.$bvModal.show("success-qc-check");
      else if (status === STIM_STATUS.SHORT_CIRCUIT_ERROR) this.$bvModal.show("short-circuit-err");
    },
    setSystemSpecificStatus: function (status) {
      switch (status) {
        case STATUS.SERVER_INITIALIZING_STATE:
          this.alertTxt = "Booting Up...";
          break;
        case STATUS.SERVER_READY_STATE:
          this.alertTxt = "Connecting...";
          break;
        case STATUS.INSTRUMENT_INITIALIZING_STATE:
          this.alertTxt = "Initializing...";
          break;
        case STATUS.CHECKING_FOR_UPDATES_STATE:
          this.alertTxt = "Checking for Firmware Updates...";
          break;
        case STATUS.UPDATES_NEEDED_STATE:
          this.alertTxt = `Firmware Updates Required`;
          break;
        case STATUS.DOWNLOADING_UPDATES_STATE:
          this.alertTxt = `Downloading Firmware Updates...`;
          this.$bvModal.show("fw-updates-in-progress-message");
          break;
        case STATUS.INSTALLING_UPDATES_STATE:
          this.alertTxt = `Installing Firmware Updates...`;
          break;
        case STATUS.UPDATES_COMPLETE_STATE:
          this.alertTxt = `Firmware Updates Complete`;
          this.closeModalsById(["fw-updates-in-progress-message", "fw-closure-warning"]);
          this.$bvModal.show("fw-updates-complete-message");
          break;
        case STATUS.UPDATE_ERROR_STATE:
          this.alertTxt = `Error During Firmware Update`;
          this.closeModalsById(["fw-updates-in-progress-message", "fw-closure-warning"]);
          this.$store.commit("system/stopStatusPinging");
          this.$store.commit("system/setShutdownErrorMessage", "Error during firmware update.");
          this.$bvModal.show("error-catch");
          break;
        case STATUS.ERROR_STATE:
          this.closeModalsById([
            "fw-updates-in-progress-message",
            "fw-closure-warning",
            "ops-closure-warning",
          ]);

          this.alertTxt = "Error Occurred";
          this.$bvModal.show("error-catch");
          break;
        default:
          this.alertTxt = status;
          break;
      }
    },

    handleConfirmation: function (idx) {
      // Tanner (1/19/22): skipping automatic closure cancellation since this method gaurantees
      // sendConfirmation will be emitted, either immediately or after closing sw-update-message
      this.closeModalsById(["ops-closure-warning", "fw-closure-warning"], false);

      // if a SW update is available, show message before confirming closure
      if (idx === 1 && this.softwareUpdateAvailable && this.allowSWUpdateInstall) {
        this.$bvModal.show("sw-update-message");
      } else {
        this.$emit("send-confirmation", idx);
      }
    },
    closeModalsById: function (ids, autoCancelClosure = true) {
      for (const id of ids) {
        this.$bvModal.hide(id);
      }

      // Tanner (1/19/22): if one of the closure warning modals is given here while there is an unresolved
      // closure confirmation, need to respond with cancel value. If this step is skipped, need to make sure
      // sendConfirmation will definitely be emitted, or the window will essentially be locked open
      if (
        autoCancelClosure &&
        this.confirmationRequest &&
        (ids.includes("ops-closure-warning") || ids.includes("fw-closure-warning"))
      ) {
        this.$emit("sendConfirmation", 0);
      } else if (ids.includes("failed-qc-check") || ids.includes("success-qc-check")) {
        this.$store.commit("stimulation/setStimStatus", STIM_STATUS.READY);
      } else if (ids.includes("error-catch")) {
        this.shutdownRequest();
      }
    },
    closeSwUpdateModal: function () {
      this.$bvModal.hide("sw-update-message");
      this.$emit("send-confirmation", 1);
    },
    shutdownRequest: async function () {
      const shutdownUrl = "http://localhost:4567/shutdown";
      try {
        await Vue.axios.get(shutdownUrl);
      } catch (error) {
        return;
      }
    },
  },
};
</script>
<style>
.div__status-bar {
  top: 0px;
  left: 0px;
  width: 287px;
  height: 40px;
  background: #1c1c1c;
  border: none;
  border-radius: 0px;
  position: relative;
}

.span__status-bar-text {
  pointer-events: all;
  line-height: 100%;
  position: absolute;
  width: 274px;
  height: 23px;
  top: 5px;
  left: 11px;
  padding: 5px;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: italic;
  text-decoration: none;
  font-size: 13px;
  color: #ffffff;
  text-align: left;
  z-index: 101;
}
.modal-backdrop {
  background-color: rgb(0, 0, 0, 0.5);
}

.modal-content {
  background-color: rgb(0, 0, 0, 0.5);
}

/* Center the error-catch pop-up dialog within the viewport */
#error-catch,
#sw-update-message,
#fw-updates-in-progress-message,
#fw-updates-complete-message,
#fw-closure-warning,
#ops-closure-warning,
#del-protocol-modal,
#add-user,
#edit-user,
#add-user,
#edit-user,
#active-processes-warning,
#initializing-warning,
#short-circuit-err,
#success-qc-check {
  position: fixed;
  margin: 5% auto;
  top: 15%;
  left: 0;
  right: 0;
}
#failed-qc-check {
  position: fixed;
  margin: 5% auto;
  top: 10%;
  left: 0;
  right: 0;
}
</style>
