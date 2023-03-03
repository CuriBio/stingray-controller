<template>
  <div class="div__status-bar">
    <span class="span__status-bar-text">{{ status_label }}: {{ alert_txt }}</span>
    <span>
      <b-modal id="error-catch" size="sm" hide-footer hide-header hide-header-close :static="true">
        <ErrorCatchWidget :log_filepath="logPath" @ok-clicked="close_modals_by_id(['error-catch'])" />
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
          :modal_labels="fw_updates_complete_labels"
          @handleConfirmation="close_modals_by_id(['fw-updates-complete-message'])"
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
          :modal_labels="short_circuit_labels"
          :email_error="true"
          @handleConfirmation="close_modals_by_id(['short-circuit-err'])"
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
        <StatusSpinnerWidget :modal_labels="fw_update_in_progress_labels" />
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
        <StatusWarningWidget :modal_labels="sw_update_labels" @handleConfirmation="close_sw_update_modal" />
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
          :modal_labels="fw_closure_warning_labels"
          @handleConfirmation="handleConfirmation"
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
        <StatusWarningWidget @handleConfirmation="handleConfirmation" />
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
        <StimQCSummary @handleConfirmation="close_modals_by_id(['failed-qc-check'])" />
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
          :modal_labels="successful_qc_check_labels"
          @handleConfirmation="close_modals_by_id(['success-qc-check'])"
        />
      </b-modal>
      <b-modal
        id="active-processes-warning"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget
          :modal_labels="active_processes_modal_labels"
          @handleConfirmation="close_da_check_modal"
        />
      </b-modal>
      <b-modal
        id="initializing-warning"
        size="sm"
        hide-footer
        hide-header
        hide-header-close
        :static="true"
        :no-close-on-backdrop="true"
      >
        <StatusWarningWidget
          :modal_labels="initializing_modal_labels"
          @handleConfirmation="close_da_check_modal"
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
 * @vue-data     {String} alert_txt - Contains the current status of the Application and its updated as status change.
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
    stim_specific: {
      type: Boolean,
      default: false,
    },
    da_check: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      alert_txt: "",
      fw_closure_warning_labels: {
        header: "Warning!",
        msg_one:
          "A firmware update for the Mantarray instrument is in progress. Closing the software now could damage the instrument.",
        msg_two: "Are you sure you want to exit?",
        button_names: ["Cancel", "Yes"],
      },
      fw_updates_complete_labels: {
        header: "Important!",
        msg_one: "Firmware updates have been successfully installed.",
        msg_two:
          "Please close the Mantarray software, power the Mantarray instrument off and on, then restart the Mantarray software.",
        button_names: ["Okay"],
      },
      sw_update_labels: {
        header: "Important!",
        msg_one: "A software update will be installed after exiting.",
        msg_two:
          "The installer may prompt you to take action while it is running. Please watch it after this software closes.",
        button_names: ["Okay"],
      },
      short_circuit_labels: {
        header: "Error!",
        msg_one:
          "A short circuit has been found during the configuration check. Replace the stimulation lid.",
        msg_two: "If the issue persists, please contact:  ",
        button_names: ["Okay"],
      },
      successful_qc_check_labels: {
        header: "Configuration Check Complete!",
        msg_one: "No open circuits were detected in a well assigned with a protocol.",
        msg_two: "You can now run this stimulation.",
        button_names: ["Okay"],
      },
      active_processes_modal_labels: {
        header: "Warning!",
        msg_one: "Data analysis cannot be performed while other processes are running.",
        msg_two: "Active processes will be automatically stopped if you choose to continue.",
        button_names: ["Cancel", "Continue"],
      },
      initializing_modal_labels: {
        header: "Warning!",
        msg_one: "Data analysis cannot be performed while the instrument is initializing or calibrating.",
        msg_two: "It will become available shortly.",
        button_names: ["Close"],
      },
      h5_warning_label: {
        header: "Error!",
        msg_one: "Corrupt h5 files found",
        msg_two: "",
        button_names: ["Close"],
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
      "beta2Mode",
      "softwareUpdateAvailable",
      "allowSWUpdateInstall",
      "firmwareUpdateDurMins",
      "confirmationRequest",
    ]),
    fw_update_in_progress_labels: function () {
      let duration = `${this.firmwareUpdateDurMins} minute`;
      if (this.firmwareUpdateDurMins !== 1) duration += "s";
      return {
        header: "Important!",
        msg_one: `The firmware update is in progress. It will take about ${duration} to complete.`,
        msg_two: "Do not close the Mantarray software or power off the Mantarray instrument.",
      };
    },
    status_label: function () {
      return this.stim_specific ? "Stim status" : "System status";
    },
    assigned_open_circuits: function () {
      // filter for matching indices
      return this.stimulatorCircuitStatuses.filter((well) =>
        Object.keys(this.protocolAssignments).includes(well.toString())
      );
    },
    is_playback_active: function () {
      return [STATUS.MESSAGE.LIVE_VIEW_ACTIVE, STATUS.MESSAGE.RECORDING, STATUS.MESSAGE.BUFFERING].includes(
        this.statusUuid
      );
    },
    is_initializing: function () {
      return [
        STATUS.MESSAGE.SERVER_BOOTING_UP,
        STATUS.MESSAGE.SERVER_STILL_INITIALIZING,
        STATUS.MESSAGE.SERVER_READY,
        STATUS.MESSAGE.INITIALIZING_INSTRUMENT,
        STATUS.MESSAGE.CALIBRATING, // this is added to be included in specific modal
      ].includes(this.statusUuid);
    },
    is_updating: function () {
      return [
        STATUS.MESSAGE.CHECKING_FOR_UPDATES,
        STATUS.MESSAGE.INSTALLING_UPDATES,
        STATUS.MESSAGE.DOWNLOADING_UPDATES,
      ].includes(this.statusUuid);
    },
    is_data_analysis_enabled: function () {
      return !this.stimPlayState && !this.is_playback_active && !this.is_initializing && !this.is_updating;
    },
  },
  watch: {
    statusUuid: function (new_status) {
      // set message for stimulation status and system status if error occurs
      if (!this.stim_specific && !this.shutdownErrorStatus) this.set_system_specific_status(new_status);
    },
    stimStatus: function (new_status) {
      if (this.stim_specific) this.set_stim_specific_status(new_status);
    },
    confirmationRequest: function () {
      const sensitive_ops_in_progress =
        this.is_playback_active ||
        this.statusUuid === STATUS.MESSAGE.CALIBRATING ||
        this.stimStatus === STIM_STATUS.CONFIG_CHECK_IN_PROGRESS ||
        this.stimPlayState ||
        this.total_uploaded_files.length < this.total_file_count ||
        this.is_recording_snapshot_running;

      const fw_update_in_progress =
        this.statusUuid === STATUS.MESSAGE.DOWNLOADING_UPDATES ||
        this.statusUuid === STATUS.MESSAGE.INSTALLING_UPDATES;

      if (this.confirmationRequest && !this.stim_specific) {
        if (fw_update_in_progress) {
          this.$bvModal.show("fw-closure-warning");
        } else if (sensitive_ops_in_progress) {
          this.$bvModal.show("ops-closure-warning");
        } else {
          this.handleConfirmation(1);
        }
      }
    },
    shutdownErrorStatus: function (new_val, _) {
      if (new_val) {
        this.close_modals_by_id([
          "fw-updates-in-progress-message",
          "fw-closure-warning",
          "ops-closure-warning",
        ]);
        this.alert_txt = "Error Occurred";
        this.$bvModal.show("error-catch");
      }
    },
  },
  created() {
    this.stim_specific
      ? this.set_stim_specific_status(this.stim_status)
      : this.set_system_specific_status(this.statusUuid);
  },
  methods: {
    set_stim_specific_status: function (status) {
      this.alert_txt = status;

      if (status === STIM_STATUS.CONFIG_CHECK_COMPLETE)
        this.assigned_open_circuits.length > 0
          ? this.$bvModal.show("failed-qc-check")
          : this.$bvModal.show("success-qc-check");
      else if (status === STIM_STATUS.SHORT_CIRCUIT_ERROR) this.$bvModal.show("short-circuit-err");
    },
    set_system_specific_status: function (status) {
      switch (status) {
        case STATUS.MESSAGE.SERVER_BOOTING_UP:
          this.alert_txt = "Booting Up...";
          break;
        case STATUS.MESSAGE.SERVER_STILL_INITIALIZING:
          this.alert_txt = "Connecting...";
          break;
        case STATUS.MESSAGE.SERVER_READY:
          this.alert_txt = "Connecting...";
          break;
        case STATUS.MESSAGE.INITIALIZING_INSTRUMENT:
          this.alert_txt = "Initializing...";
          break;
        case STATUS.MESSAGE.CALIBRATION_NEEDED:
          this.alert_txt = `Connected...Calibration Needed`;
          break;
        case STATUS.MESSAGE.CALIBRATING:
          this.alert_txt = `Calibrating...`;
          break;
        case STATUS.MESSAGE.CALIBRATED:
          this.alert_txt = `Ready`;
          break;
        case STATUS.MESSAGE.BUFFERING:
          this.alert_txt = `Preparing for Live View...`;
          break;
        case STATUS.MESSAGE.LIVE_VIEW_ACTIVE:
          this.alert_txt = `Live View Active`;
          break;
        case STATUS.MESSAGE.RECORDING:
          this.alert_txt = `Recording to File...`;
          break;
        case STATUS.MESSAGE.CHECKING_FOR_UPDATES:
          this.alert_txt = "Checking for Firmware Updates...";
          break;
        case STATUS.MESSAGE.UPDATES_NEEDED:
          this.alert_txt = `Firmware Updates Required`;
          break;
        case STATUS.MESSAGE.DOWNLOADING_UPDATES:
          this.alert_txt = `Downloading Firmware Updates...`;
          this.$bvModal.show("fw-updates-in-progress-message");
          break;
        case STATUS.MESSAGE.INSTALLING_UPDATES:
          this.alert_txt = `Installing Firmware Updates...`;
          break;
        case STATUS.MESSAGE.UPDATES_COMPLETE:
          this.alert_txt = `Firmware Updates Complete`;
          this.close_modals_by_id(["fw-updates-in-progress-message", "fw-closure-warning"]);
          this.$bvModal.show("fw-updates-complete-message");
          break;
        case STATUS.MESSAGE.UPDATE_ERROR:
          this.alert_txt = `Error During Firmware Update`;
          this.close_modals_by_id(["fw-updates-in-progress-message", "fw-closure-warning"]);
          this.$store.commit("flask/stopStatusPinging");
          this.$store.commit("settings/setShutdownErrorMessage", "Error during firmware update.");
          this.$bvModal.show("error-catch");
          break;
        case STATUS.MESSAGE.ERROR:
          this.close_modals_by_id([
            "fw-updates-in-progress-message",
            "fw-closure-warning",
            "ops-closure-warning",
          ]);

          this.alert_txt = "Error Occurred";
          this.$bvModal.show("error-catch");
          break;
        default:
          this.alert_txt = status;
          break;
      }
    },

    handleConfirmation: function (idx) {
      // Tanner (1/19/22): skipping automatic closure cancellation since this method gaurantees
      // send_confirmation will be emitted, either immediately or after closing sw-update-message
      this.close_modals_by_id(["ops-closure-warning", "fw-closure-warning"], false);

      // if a SW update is available, show message before confirming closure
      if (idx === 1 && this.softwareUpdateAvailable && this.allowSWUpdateInstall) {
        this.$bvModal.show("sw-update-message");
      } else {
        this.$emit("send_confirmation", idx);
      }
    },
    close_modals_by_id: function (ids, auto_cancel_closure = true) {
      for (const id of ids) {
        this.$bvModal.hide(id);
      }

      // Tanner (1/19/22): if one of the closure warning modals is given here while there is an unresolved
      // closure confirmation, need to respond with cancel value. If this step is skipped, need to make sure
      // send_confirmation will definitely be emitted, or the window will essentially be locked open
      if (
        auto_cancel_closure &&
        this.confirmationRequest &&
        (ids.includes("ops-closure-warning") || ids.includes("fw-closure-warning"))
      ) {
        this.$emit("send_confirmation", 0);
      } else if (ids.includes("failed-qc-check") || ids.includes("success-qc-check")) {
        this.$store.commit("stimulation/setStimStatus", STIM_STATUS.READY);
      } else if (ids.includes("error-catch")) {
        this.shutdown_request();
      }
    },
    close_sw_update_modal: function () {
      this.$bvModal.hide("sw-update-message");
      this.$emit("send_confirmation", 1);
    },
    shutdown_request: async function () {
      const shutdown_url = "http://localhost:4567/shutdown";
      try {
        await Vue.axios.get(shutdown_url);
      } catch (error) {
        return;
      }
    },
    close_da_check_modal: function (idx) {
      this.$bvModal.hide("active-processes-warning");
      this.$bvModal.hide("initializing-warning");

      if (idx === 1) {
        if (this.stimPlayState) this.$store.dispatch("stimulation/stopStimulation");
      }

      this.$emit("close_da_check_modal", idx);
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
#success-qc-check,
#h5_warning,
#new-assignment-modal {
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
