<template>
  <div class="div__status-bar">
    <span class="span__status-bar-text">{{ statusLabel }}: {{ alertTxt }}</span>
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
import { STATUS } from "@/store/modules/flask/enums";
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
/**
 * @vue-data     {String} alertTxt - Contains the current status of the Application and its updated as status change.
 * @vue-computed {String} statusUuid - Contains a UUID which represents a meaningful information, from Vuex store.
 * @vue-event    {Event} statusUuid - A function which is invoked when UUID is modified in the Vuex store.
 */
export default {
  name: "StatusBar",
  components: {
    ErrorCatchWidget,
    StatusWarningWidget,
    StatusSpinnerWidget,
    StimQCSummary,
  },
  props: {
    stimSpecific: {
      type: Boolean,
      default: false,
    },
    daCheck: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      alertTxt: "",
      fwClosureWarningLabels: {
        header: "Warning!",
        msgOne:
          "A firmware update for the Mantarray instrument is in progress. Closing the software now could damage the instrument.",
        msgTwo: "Are you sure you want to exit?",
        buttonNames: ["Cancel", "Yes"],
      },
      fwUpdatesCompleteLabels: {
        header: "Important!",
        msgOne: "Firmware updates have been successfully installed.",
        msgTwo:
          "Please close the Mantarray software, power the Mantarray instrument off and on, then restart the Mantarray software.",
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
      activeProcessesModalLabels: {
        header: "Warning!",
        msgOne: "Data analysis cannot be performed while other processes are running.",
        msgTwo: "Active processes will be automatically stopped if you choose to continue.",
        buttonNames: ["Cancel", "Continue"],
      },
      initializingModalLabels: {
        header: "Warning!",
        msgOne: "Data analysis cannot be performed while the instrument is initializing or calibrating.",
        msgTwo: "It will become available shortly.",
        buttonNames: ["Close"],
      },
    };
  },
  computed: {
    ...mapGetters({
      statusUuid: "flask/statusId",
    }),
    ...mapState("stimulation", [
      "stimulatorCircuitStatuses",
      "protocolAssignments",
      "stimPlayState",
      "stimStatus",
    ]),
    ...mapState("settings", [
      "logPath",
      "shutdownErrorStatus",
      "softwareUpdateAvailable",
      "allowSWUpdateInstall",
      "firmwareUpdateDurMins",
      "confirmationRequest",
    ]),
    fwUpdateInProgressLabels: function () {
      let duration = `${this.firmwareUpdateDurMins} minute`;
      if (this.firmwareUpdateDurMins !== 1) duration += "s";
      return {
        header: "Important!",
        msgOne: `The firmware update is in progress. It will take about ${duration} to complete.`,
        msgTwo: "Do not close the Mantarray software or power off the Mantarray instrument.",
      };
    },
    statusLabel: function () {
      return this.stimSpecific ? "Stim status" : "System status";
    },
    assignedOpenCircuits: function () {
      // filter for matching indices
      return this.stimulatorCircuitStatuses.filter((well) =>
        Object.keys(this.protocolAssignments).includes(well.toString())
      );
    },
    isInitializing: function () {
      return [
        STATUS.MESSAGE.SERVER_BOOTING_UP,
        STATUS.MESSAGE.SERVER_STILL_INITIALIZING,
        STATUS.MESSAGE.SERVER_READY,
        STATUS.MESSAGE.INITIALIZING_INSTRUMENT,
        STATUS.MESSAGE.CALIBRATING, // this is added to be included in specific modal
      ].includes(this.statusUuid);
    },
    isUpdating: function () {
      return [
        STATUS.MESSAGE.CHECKING_FOR_UPDATES,
        STATUS.MESSAGE.INSTALLING_UPDATES,
        STATUS.MESSAGE.DOWNLOADING_UPDATES,
      ].includes(this.statusUuid);
    },
  },
  watch: {
    statusUuid: function (newStatus) {
      // set message for stimulation status and system status if error occurs
      if (!this.stimSpecific && !this.shutdownErrorStatus) this.setSystemSpecificStatus(newStatus);
    },
    stimStatus: function (newStatus) {
      if (this.stimSpecific) this.setStimSpecificStatus(newStatus);
    },
    confirmationRequest: function () {
      const sensitiveOpsInProgress =
        this.statusUuid === STATUS.MESSAGE.CALIBRATING ||
        this.stimStatus === STIM_STATUS.CONFIG_CHECK_IN_PROGRESS ||
        this.stimPlayState ||
        this.totalUploadedFiles.length < this.totalFileCount;

      const fwUpdateInProgress =
        this.statusUuid === STATUS.MESSAGE.DOWNLOADING_UPDATES ||
        this.statusUuid === STATUS.MESSAGE.INSTALLING_UPDATES;

      if (this.confirmationRequest && !this.stimSpecific) {
        if (fwUpdateInProgress) {
          this.$bvModal.show("fw-closure-warning");
        } else if (sensitiveOpsInProgress) {
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
    this.stimSpecific
      ? this.setStimSpecificStatus(this.stimStatus)
      : this.setSystemSpecificStatus(this.statusUuid);
  },
  methods: {
    setStimSpecificStatus: function (status) {
      this.alertTxt = status;

      if (status === STIM_STATUS.CONFIG_CHECK_COMPLETE)
        this.assignedOpenCircuits.length > 0
          ? this.$bvModal.show("failed-qc-check")
          : this.$bvModal.show("success-qc-check");
      else if (status === STIM_STATUS.SHORT_CIRCUIT_ERROR) this.$bvModal.show("short-circuit-err");
    },
    setSystemSpecificStatus: function (status) {
      switch (status) {
        case STATUS.MESSAGE.SERVER_BOOTING_UP:
          this.alertTxt = "Booting Up...";
          break;
        case STATUS.MESSAGE.SERVER_STILL_INITIALIZING:
          this.alertTxt = "Connecting...";
          break;
        case STATUS.MESSAGE.SERVER_READY:
          this.alertTxt = "Connecting...";
          break;
        case STATUS.MESSAGE.INITIALIZING_INSTRUMENT:
          this.alertTxt = "Initializing...";
          break;
        case STATUS.MESSAGE.CALIBRATION_NEEDED:
          this.alertTxt = `Connected...Calibration Needed`;
          break;
        case STATUS.MESSAGE.CALIBRATING:
          this.alertTxt = `Calibrating...`;
          break;
        case STATUS.MESSAGE.CALIBRATED:
          this.alertTxt = `Ready`;
          break;
        case STATUS.MESSAGE.BUFFERING:
          this.alertTxt = `Preparing for Live View...`;
          break;
        case STATUS.MESSAGE.LIVE_VIEW_ACTIVE:
          this.alertTxt = `Live View Active`;
          break;
        case STATUS.MESSAGE.RECORDING:
          this.alertTxt = `Recording to File...`;
          break;
        case STATUS.MESSAGE.CHECKING_FOR_UPDATES:
          this.alertTxt = "Checking for Firmware Updates...";
          break;
        case STATUS.MESSAGE.UPDATES_NEEDED:
          this.alertTxt = `Firmware Updates Required`;
          break;
        case STATUS.MESSAGE.DOWNLOADING_UPDATES:
          this.alertTxt = `Downloading Firmware Updates...`;
          this.$bvModal.show("fw-updates-in-progress-message");
          break;
        case STATUS.MESSAGE.INSTALLING_UPDATES:
          this.alertTxt = `Installing Firmware Updates...`;
          break;
        case STATUS.MESSAGE.UPDATES_COMPLETE:
          this.alertTxt = `Firmware Updates Complete`;
          this.closeModalsById(["fw-updates-in-progress-message", "fw-closure-warning"]);
          this.$bvModal.show("fw-updates-complete-message");
          break;
        case STATUS.MESSAGE.UPDATE_ERROR:
          this.alertTxt = `Error During Firmware Update`;
          this.closeModalsById(["fw-updates-in-progress-message", "fw-closure-warning"]);
          this.$store.commit("flask/stopStatusPinging");
          this.$store.commit("settings/setShutdownErrorMessage", "Error during firmware update.");
          this.$bvModal.show("error-catch");
          break;
        case STATUS.MESSAGE.ERROR:
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
