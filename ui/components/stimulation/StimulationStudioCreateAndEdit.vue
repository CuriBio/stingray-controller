<template>
  <div class="div__simulationstudio-backdrop">
    <span class="span__stimulationstudio-layout-create_edit-header-label"
      >Create/Edit Stimulation Protocol</span
    >
    <span class="span__stimulationstudio-layout-subheader-label">Select/Create Protocol</span>
    <div class="div__stimulationstudio-select-dropdown-container">
      <SelectDropDown
        :optionsText="protocolList"
        :optionsIdx="selectedProtocolIdx"
        :inputWidth="inputWidth"
        :inputHeight="inputHeight"
        @selection-changed="selectedProtocolChange"
      />
    </div>
    <canvas class="canvas__stimulationstudio-button-separator" />
    <div
      v-for="(key, value, idx) in btnLabels"
      :id="value"
      :key="value"
      v-b-popover.hover.bottom="selectionBtnDetails(idx).tooltip || ''"
      :class="getClass(idx)"
      :style="key"
      @click.exact="handleClick(idx)"
    >
      <span :class="getLabelClass(idx)">{{ value }}</span>
    </div>
    <div
      v-for="(key, value, idx) in importExportBtnLabels"
      id="importExportButton"
      :key="value"
      @click.exact="handleImportExport(idx)"
    >
      <div :class="'div__stimulationstudio-btn-container'" :style="key">
        <span type="button" :class="'span__stimulationstudio-btn-label'">{{ value }}</span>
      </div>
    </div>
  </div>
</template>
<script>
import SelectDropDown from "@/components/basic-widgets/SelectDropDown.vue";
import { mapActions, mapMutations, mapState } from "vuex";

/**
 * @vue-data {Object} btnLabels - Label and style of buttons
 * @vue-data {Object} importExportBtnLabels - Label and style of export and import buttons
 * @vue-data {Int} selectedProtocolIdx - Index of selected protocol from dropdown
 * @vue-data {Int} inputHeight - Height passed down to dropdown for styling
 * @vue-data {Int} inputWidth -  Width passed down to dropdown for styling
 * @vue-data {Array} protocolList - Availble protocols to display in dropdown
 * @vue-event {Event} selectedProtocolChange - Changes when a new protocol is selected from dropdown
 * @vue-event {Event} handleClick - Performs functions based on which button is clicked regarding assigning and clearing protocols from plate editor
 * @vue-event {Event} getClass - Dynamically renders button class depending on if button is disabled
 * @vue-event {Event} getLabelClass - Dynamically renders button labels class depending on if button is disabled
 * @vue-event {Event} handleImportExport - On click, it reassigns function to input[type=file] to upload file
 * @vue-event {Event} handleImport - Dispatches imported file to be handled in store
 * @vue-event {Event} handleExport - Dispatches request to store to write current protocol
 */

const NUM_CLUSTERS = 24;
const CLUSTER_SIZE = 4;

export default {
  name: "StimulationStudioCreateAndEdit",
  components: {
    SelectDropDown,
  },
  props: {
    disableEdits: { type: Boolean, default: false },
  },
  data() {
    return {
      btnLabels: {
        "Apply to Selection": " left: 19%; top: 49%; ",
        "Clear Selection": " left: 51%; top: 49%; ",
      },
      importExportBtnLabels: {
        "Import Protocol(s)": " left: 19%; top: 76%; width: 30%;",
        "Export Protocol(s)": " left: 51%; top: 76%; width: 30%;",
      },
      selectedProtocolIdx: 0,
      inputHeight: 45,
      inputWidth: 600,
    };
  },
  computed: {
    ...mapState("stimulation", ["protocolList", "editMode", "protocolAssignments", "selectedWells"]),
    editModeStatus: function () {
      return this.editMode.status;
    },
    noWellsSelected: function () {
      return this.selectedWells.length === 0;
    },
    oneProtocolPerClusterAfterApply: function () {
      const selectedProtocolLetter = (this.protocolList[this.selectedProtocolIdx] || {}).letter;
      if (selectedProtocolLetter == null || selectedProtocolLetter === "") {
        // if no protocol selected, then applying shouldn't be possible, just return true
        return true;
      }
      const selectedWellsSet = new Set(this.selectedWells);
      // check that rule is not violated in any cluster
      for (let clusterIdx = 0; clusterIdx < NUM_CLUSTERS; clusterIdx++) {
        let protocolOfCluster = null;
        for (let baseWellIdx = 0; baseWellIdx < CLUSTER_SIZE; baseWellIdx++) {
          const wellIdx = clusterIdx * CLUSTER_SIZE + baseWellIdx;
          // get protocol (if any) that would be assigned to the well after applying the current protocol to the selection
          let protocolOfWell;
          if (selectedWellsSet.has(wellIdx)) {
            // if well is selected, use the selected protocol
            protocolOfWell = selectedProtocolLetter;
          } else {
            // otherwise use the protocol currently assigned to the well, if any
            protocolOfWell = (this.protocolAssignments[wellIdx] || {}).letter;
          }
          // if no protocol assigned to this well after applying, then no need to check further
          if (protocolOfWell == null) {
            continue;
          }
          if (protocolOfCluster === null) {
            // if this is the first well encountered in the cluster that is assigned a protocol, then use
            // it to compare subsequent well assignments against
            protocolOfCluster = protocolOfWell;
          } else if (protocolOfWell !== protocolOfCluster) {
            // applying would cause this well to have a different protocol assigned than another well in the cluster
            return false;
          }
        }
      }
      return true;
    },
  },
  watch: {
    protocolList: function (newList, oldList) {
      if (newList.length !== oldList.length) this.selectedProtocolIdx = 0;
    },
    editModeStatus: function () {
      if (!this.editModeStatus) this.selectedProtocolIdx = 0;
    },
  },
  methods: {
    ...mapActions("stimulation", ["editSelectedProtocol", "handleImportProtocol", "handleExportProtocol"]),
    ...mapMutations("stimulation", [
      "setEditModeOff",
      "resetProtocolEditor",
      "clearSelectedProtocol",
      "applySelectedProtocol",
    ]),
    async selectedProtocolChange(idx) {
      this.selectedProtocolIdx = idx;
      const selectedProtocol = this.protocolList[idx];

      if (idx === 0) {
        this.setEditModeOff();
        this.resetProtocolEditor();
      } else await this.editSelectedProtocol(selectedProtocol);

      this.$emit("handle-selection-change", selectedProtocol);
    },
    selectionBtnDetails(idx) {
      if (this.disableEdits) {
        return { disabled: true };
      } else if (this.noWellsSelected) {
        return { disabled: true, tooltip: "No wells selected." };
      } else if (idx === 0) {
        // Apply btn
        if (this.selectedProtocolIdx === 0) {
          return { disabled: true, tooltip: "Cannot apply this protocol until it is saved." };
        } else if (!this.oneProtocolPerClusterAfterApply) {
          return {
            disabled: true,
            tooltip:
              "Applying this protocol to the selected wells would violate the one-protocol-per-cluster requirement.",
          };
        } else {
          return { disabled: false };
        }
      } else {
        // Clear btn
        return { disabled: false };
      }
    },
    handleClick(idx) {
      if (this.selectionBtnDetails(idx).disabled) {
        return;
      }

      if (idx === 0) {
        const selectedProtocol = this.protocolList[this.selectedProtocolIdx];
        this.applySelectedProtocol(selectedProtocol);
      } else if (idx === 1) {
        this.clearSelectedProtocol();
      }
    },
    getClass(idx) {
      return this.selectionBtnDetails(idx).disabled
        ? "div__stimulationstudio-btn-container-disable"
        : "div__stimulationstudio-btn-container";
    },
    getLabelClass(idx) {
      return this.selectionBtnDetails(idx).disabled
        ? "span__stimulationstudio-btn-label-disable"
        : "span__stimulationstudio-btn-label";
    },
    handleImportExport(idx) {
      if (idx === 0) {
        // this adds and removes the input element to be able to allow importing the same file twice in a row.
        // Otherwise the @change event won't get triggered if the same file is selected twice.
        const inputEl = document.createElement("input");
        document.body.appendChild(inputEl);
        inputEl.setAttribute("ref", "file");
        inputEl.setAttribute("type", "file");
        inputEl.addEventListener("change", (e) => this.handleImport(e.target.files));
        inputEl.click();
        inputEl.remove();
      } else if (idx === 1) {
        this.handleExport();
      }
    },
    handleImport(file) {
      this.handleImportProtocol(file[0]);
    },
    handleExport() {
      this.handleExportProtocol();
    },
  },
};
</script>

<style scoped>
.div__simulationstudio-backdrop {
  display: flex;
  justify-content: center;
  box-sizing: border-box;
  background: rgb(17, 17, 17);
  position: absolute;
  width: 640px;
  height: 280px;
  visibility: visible;
  border-radius: 10px;
  box-shadow: rgba(0, 0, 0, 0.7) 0px 0px 10px 0px;
  pointer-events: all;
  z-index: 2;
}

.span__stimulationstudio-layout-create_edit-header-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  padding-top: 15px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-size: 19px;
  color: rgb(255, 255, 255);
  text-align: center;
}

.span__stimulationstudio-layout-subheader-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  top: 45px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
}

.div__stimulationstudio-select-dropdown-container {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  position: absolute;
  width: 210px;
  height: 50px;
  top: 75px;
  right: 410px;
  padding: 5px;
  z-index: 3;
}

.div__stimulationstudio-select-dropdown-container > .div__input-dropdown-background {
  background: none;
  border: none;
}

.div__stimulationstudio-btn-container {
  display: flex;
  justify-content: center;
  align-content: center;
  position: absolute;
  width: 30%;
  height: 45px;
  background: #b7b7b7;
}

.div__stimulationstudio-btn-container-disable {
  display: flex;
  justify-content: center;
  align-content: center;
  position: absolute;
  width: 30%;
  height: 45px;
  background: #b7b7b7c9;
}

.div__stimulationstudio-btn-container:hover {
  background: #b7b7b7c9;
  cursor: pointer;
}

.span__stimulationstudio-btn-label {
  transform: translateZ(0px);
  line-height: 45px;
  font-family: Muli;
  font-size: 16px;
  color: rgb(0, 0, 0);
}

.span__stimulationstudio-btn-label-disable {
  transform: translateZ(0px);
  line-height: 45px;
  font-family: Muli;
  font-size: 16px;
  color: #6e6f72;
}

.canvas__stimulationstudio-button-separator {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  width: 620px;
  height: 2px;
  top: 70%;
  visibility: visible;
  background-color: #3f3f3f;
  opacity: 0.5;
}
</style>
