<template>
  <div class="div__BlockViewEditor-background">
    <div class="div__Tabs-panel">
      <span
        :id="'Basic'"
        :class="activeTab === 'Advanced' ? 'span__Inactive-Tab-labels' : 'span__Active-Tab-label'"
        @click="toggleTab($event.target.id)"
        >Basic</span
      >
      <span
        :id="'Advanced'"
        :class="activeTab === 'Basic' ? 'span__Inactive-Tab-labels' : 'span__Active-Tab-label'"
        @click="toggleTab($event.target.id)"
        >Advanced</span
      >
    </div>
    <div class="div__Editor-background">
      <div class="div__setting-panel-container">
        <span :key="currentLetter" class="span__protocol-letter" :style="'color:' + currentColor">{{
          currentLetter
        }}</span>
        <input
          v-model="protocolName"
          class="protocol_name_input"
          placeholder="Protocol Name"
          :style="nameValidity"
          @change="(e) => (protocolName = e.target.value)"
        />
        <span class="error-message">{{ errorMessage }}</span>
        <div class="div__right-settings-panel">
          <SmallDropDown
            :inputHeight="25"
            :inputWidth="200"
            :disableSelection="true"
            :optionsText="stimulationTypesArray"
            :optionsIdx="stimulationTypeIdx"
            :domIdSuffix="'stimulationType'"
            @selection-changed="handleStimulationType"
          />
          <SmallDropDown
            :style="'margin-left: 5%;'"
            :inputHeight="25"
            :inputWidth="176"
            :optionsText="stopOptionsArray"
            :optionsIdx="stopOptionIdx"
            :domIdSuffix="'stopOptions'"
            @selection-changed="handleStopSetting"
          />
          <span class="span__settings-label">every</span>
          <div v-b-popover.hover.bottom="restInputHover" class="number-input-container">
            <InputWidget
              :style="'position: relative;'"
              :initialValue="restDuration"
              :placeholder="'0'"
              :domIdSuffix="'protocol-rest'"
              :invalidText="invalidRestDurText"
              :disabled="disabledTime"
              :inputWidth="100"
              :inputHeight="25"
              :topAdjust="-2"
              @update:value="handleRestDuration($event)"
            />
          </div>
          <FontAwesomeIcon
            id="trashIcon"
            class="trash-icon"
            :icon="['fa', 'trash-alt']"
            @click="openDelModal"
          />
        </div>
      </div>
    </div>
    <b-modal
      :id="'del-protocol-modal'"
      size="sm"
      hide-footer
      hide-header
      hide-header-close
      :static="true"
      :no-close-on-backdrop="true"
    >
      <StatusWarningWidget
        id="del-protocol"
        :modalLabels="delProtocolLabels"
        @handleConfirmation="closeDelProtocolModal"
      />
    </b-modal>
  </div>
</template>
<script>
import Vue from "vue";
import SmallDropDown from "@/components/basic-widgets/SmallDropDown.vue";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faTrashAlt } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import StatusWarningWidget from "@/components/status/StatusWarningWidget.vue";
import BootstrapVue from "bootstrap-vue";
import { BModal } from "bootstrap-vue";
import InputWidget from "@/components/basic-widgets/InputWidget.vue";
import { MAX_SUBPROTOCOL_DURATION_MS } from "@/store/modules/stimulation/enums";
Vue.use(BootstrapVue);
Vue.component("BModal", BModal);
library.add(faTrashAlt);

/**
 * @vue-data {String} activeTab - Shows current selected tab
 * @vue-data {Boolean} disabled - Disables the name and time input fields
 * @vue-data {String} currentLetter - Next available letter in alphabet
 * @vue-data {String} currentColor -  Next available color in alphabet
 * @vue-data {Array} stimulationTypesArray - Availble options in dropdown
 * @vue-data {Array} stopOptionsArray - Available options in dropdown
 * @vue-data {String} protocolName - Inputted new protocol name
 * @vue-data {String} stopSetting - Selected setting from dropdown
 * @vue-data {String} restDuration - Inputted delay to be set at the end of the protocol between repeats
 * @vue-data {String} nameValidity - Corresponding border style after name validity check
 * @vue-data {String} errorMessage - Error message that appears under name input field after validity check
 * @vue-data {Array} localProtocolList - All available protocols from Vuex
 * @vue-data {Int} stimulationTypeIdx - Used to change preselected index in the dropdown when user wants to edit existing protocols
 * @vue-event {Event} updateProtocols - Gets called when a change to the available protocol list occurs to update next available color/letter assignment and dropdown options
 * @vue-event {Event} handleTrashModal - Toggle view of delete popover on trash icon
 * @vue-event {Event} toggleTab - Toggles which tab is active
 * @vue-event {Event} handleDelete - Confirms and commits the deletion of protocol to state
 * @vue-event {Event} handleStimulationType - Commits the new selected stimulation type to state
 * @vue-event {Event} handleStopSetting - Currently just assigns the new stop setting to local state
 * @vue-event {Event} handleRestDuration - Commits the new delay input to state
 * @vue-event {Event} checkNameValidity - Checks if the inputted name has already been used
 */

export default {
  name: "StimulationStudioProtocolBlockViewEditor",
  components: {
    SmallDropDown,
    FontAwesomeIcon,
    StatusWarningWidget,
    InputWidget,
  },
  data() {
    return {
      activeTab: "Basic",
      disabledTime: false,
      currentLetter: "",
      currentColor: "",
      stimulationTypesArray: ["Current Controlled Stimulation", "(Not Yet Available)"],
      stopOptionsArray: ["Stimulate Until Stopped", "Stimulate Until Complete"],
      protocolName: "",
      stopOptionIdx: 0,
      stimulationTypeIdx: 0,
      restDuration: "",
      nameValidity: "null",
      errorMessage: "",
      localProtocolList: [],
      delProtocolLabels: {
        header: "Warning!",
        msgOne: "You are about to permanently delete this protocol.",
        msgTwo: "Please confirm to continue.",
        buttonNames: ["Delete", "Cancel"],
      },
      invalidRestDurText: "",
    };
  },
  computed: {
    ...mapState("stimulation", ["protocolEditor", "editMode", "protocolList"]),
    ...mapGetters("stimulation", ["getNextProtocol"]),
    restInputHover: function () {
      return {
        content: 'Cannot set this value if using "Stimulate Until Complete"',
        disabled: !this.disabledTime,
      };
    },
    restTimeUnit: function () {
      return this.protocolEditor.restTimeUnit;
    },
    editModeStatus: function () {
      return this.editMode.status;
    },
    editModeLabel: function () {
      return this.editMode.label;
    },
  },
  watch: {
    protocolEditor: function () {
      this.setProtocolForEdit();
    },
    restTimeUnit() {
      if (!this.disabledTime) {
        this.handleRestDuration(this.restDuration);
      }
    },
    editModeStatus: function () {
      this.setProtocolForEdit();
    },
    editModeLabel: function () {
      this.setProtocolForEdit();
    },
    protocolName: function () {
      this.checkNameValidity(this.protocolName);
    },
  },
  created() {
    this.updateProtocols();
  },
  mounted() {
    this.$store.commit("stimulation/setEditModeOff");
    this.updateProtocols();
  },
  methods: {
    ...mapActions("stimulation", ["handleProtocolEditorReset", "handleNewRestDuration"]),
    ...mapMutations("stimulation", ["setStimulationType", "setProtocolName", "setStopSetting"]),
    updateProtocols() {
      this.localProtocolList = this.protocolList;
      const { letter, color } = this.getNextProtocol;
      this.currentLetter = letter;
      this.currentColor = color;
    },
    setProtocolForEdit() {
      this.updateProtocols();
      const { name, restDuration, runUntilStopped, stimulationType } = this.protocolEditor;

      this.protocolName = name;
      this.restDuration = JSON.stringify(restDuration);
      this.stimulationTypeIdx = +(stimulationType === "V");
      this.stopOptionIdx = +!runUntilStopped;
      this.disabledTime = !runUntilStopped;
    },
    toggleTab(tab) {
      this.activeTab = tab === "Basic" ? "Basic" : "Advanced";
    },
    openDelModal() {
      this.$bvModal.show("del-protocol-modal");
    },
    closeDelProtocolModal(idx) {
      this.$bvModal.hide("del-protocol-modal");
      if (idx === 0) this.handleProtocolEditorReset();
    },
    handleStimulationType(idx) {
      const type = this.stimulationTypesArray[idx];
      this.stimulationTypeIdx = idx;
      this.setStimulationType(type);
    },
    handleStopSetting(idx) {
      const setting = this.stopOptionsArray[idx];
      this.stopOptionIdx = idx;
      this.disabledTime = idx === 1;

      if (this.disabledTime) this.handleRestDuration("0");

      this.setStopSetting(setting.includes("Stopped"));
    },
    handleRestDuration(time) {
      const timeInt = +time;
      this.restDuration = time;
      if (isNaN(timeInt) || timeInt < 0) {
        this.invalidRestDurText = "Must be a (+) number";
      } else if (this.getDurInMs(timeInt) > MAX_SUBPROTOCOL_DURATION_MS) {
        this.invalidRestDurText = "Must be <= 24hrs";
      } else {
        this.invalidRestDurText = "";
        this.handleNewRestDuration(this.restDuration);
      }

      const restDurIsValid = this.invalidRestDurText === "";
      this.$emit("new-rest-dur", restDurIsValid);
    },
    getDurInMs(value) {
      return this.restTimeUnit === "milliseconds" ? value : value * 1000;
    },
    checkNameValidity(input) {
      const matchedNames = this.localProtocolList.filter((protocol) => {
        return protocol.label === input;
      });

      if (input === "") {
        this.nameValidity = "";
        this.errorMessage = "";
      } else if (matchedNames.length === 0 || this.editModeLabel === input) {
        this.nameValidity = "border: 1px solid #19ac8a";
        this.errorMessage = "";
        this.setProtocolName(input);
      } else {
        this.nameValidity = "border: 1px solid #bd3532";
        this.errorMessage = "*Protocol name already exists";
      }
    },
  },
};
</script>
<style scoped>
.div__BlockViewEditor-background {
  background: rgb(0, 0, 0);
  position: absolute;
  border-radius: 10px;
  width: 1315px;
  font-family: muli;
}

.error-message {
  color: #bd3532;
  position: absolute;
  left: 53px;
  top: 36px;
  font-size: 13px;
  font-style: italic;
}

.span__settings-label {
  color: rgb(255, 255, 255);
  height: 8px;
  padding: 10px;
  font-size: 12px;
  margin-bottom: 2%;
  margin-left: 3%;
}

.div__setting-panel-container {
  position: absolute;
  width: 100%;
  height: 40px;
  display: flex;
  top: 1%;
  align-items: center;
}

.span__protocol-letter {
  position: relative;
  left: 2%;
  font-weight: bold;
  font-size: 25px;
}

.trash-icon {
  margin-left: 11%;
  margin-right: 4px;
  color: #4c4c4c;
  padding-top: 1px;
  font-size: 20px;
}

.trash-icon:hover {
  cursor: pointer;
  opacity: 0.6;
}

.div__right-settings-panel {
  left: 1000px;
  width: 90%;
  display: flex;
  justify-self: flex-end;
  justify-content: flex-end;
  align-items: center;
  margin: 5px;
}

.number-input-container {
  height: 25px;
  width: 100px;
  border: none;
  color: #b7b7b7;
  font-size: 12px;
  margin-right: 1%;
  text-align: center;
}

.div__heatmap-layout-minimum-input-container {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 121px;
  height: 59px;
  top: 196px;
  left: 1473.44px;
  visibility: visible;
}

.protocol_name_input {
  background: rgb(0, 0, 0);
  height: 25px;
  width: 300px;
  left: 3%;
  position: relative;
  border: none;
  padding: 0 10px 0 10px;
  color: rgb(255, 255, 255);
}

.protocol_name_input:focus {
  border: 1px solid #b7b7b7;
}

.span__Inactive-Tab-labels {
  background: rgb(8, 8, 8);
  border: 2px solid rgb(17, 17, 17);
  width: 50%;
  height: 28px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #b7b7b7b7;
}

.span__Active-Tab-label {
  width: 50%;
  height: 90%;
  background: rgb(17, 17, 17);
  display: flex;
  justify-content: center;
  align-items: center;
  color: #b7b7b7;
}

.div__Editor-background {
  transform: rotate(0deg);
  background: rgb(17, 17, 17);
  width: 1315px;
  height: 166px;
}

.div__Tabs-panel {
  background: rgb(17, 17, 17);
  width: 200px;
  height: 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  cursor: pointer;
}
</style>
