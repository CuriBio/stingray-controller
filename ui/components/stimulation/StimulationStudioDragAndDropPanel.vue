<template>
  <div>
    <div :class="modalType !== null || openDelayModal || openRepeatModal ? 'modal_overlay' : null">
      <div>
        <div class="div__DragAndDdrop-panel">
          <span class="span__stimulationstudio-drag-drop-header-label">Drag/Drop Waveforms</span>
          <canvas class="canvas__stimulationstudio-header-separator" />
          <div v-if="disableEdits" v-b-popover.hover.bottom="sidebarBlockLabel" class="div__sidebar-block" />
          <draggable
            v-model="iconTypes"
            tag="div"
            class="draggable_tile_container"
            :disabled="disableEdits"
            :group="{ name: 'order', pull: 'clone', put: false }"
            :clone="clone"
            @start="isDragging = true"
            @end="isDragging = false"
          >
            <div v-for="(type, idx) in iconTypes" :id="type" :key="idx">
              <img :src="require(`@/assets/img/${type}.png`)" />
            </div>
          </draggable>
        </div>
        <SmallDropDown
          class="dropdown-container"
          :inputHeight="25"
          :disable="disableDropdown"
          :inputWidth="100"
          :optionsText="timeUnitsArray"
          :optionsIdx="timeUnitsIdx"
          :domIdSuffix="'timeUnits'"
          :style="disableDropdown ? 'cursor: unset;' : null"
          @selection-changed="handleTimeUnit"
        />
        <div class="div__scroll-container">
          <draggable
            v-model="protocolOrder"
            class="dragArea"
            :disabled="disableEdits"
            :group="{ name: 'order' }"
            :ghost-class="'ghost'"
            @change="checkType($event)"
            @start="startDragging"
            @end="isDragging = false"
          >
            <div
              v-for="(pulse, idx) in protocolOrder"
              :key="idx"
              :class="'div__repeat-container'"
              :style="getBorderStyle(pulse)"
            >
              <!-- Only display circular icon when nested loop, icon displays number of loops -->
              <div v-if="pulse.numInterations" :class="'div__repeat-label-container'">
                <div class="div__circle" @dblclick="openRepeatModalForEdit(pulse.numInterations, idx)">
                  <span :class="'span__repeat-label'">
                    {{ pulse.numInterations }}
                  </span>
                </div>
              </div>
              <img
                v-if="pulse.type !== 'loop'"
                id="img__waveform-tile"
                :src="require(`@/assets/img/${pulse.type}.png`)"
                @dblclick="openModalForEdit(pulse.type, idx)"
                @mouseenter="onPulseEnter(idx)"
                @mouseleave="onPulseLeave"
              />
              <!-- Below is nested dropzone, can be disabled if needed -->
              <draggable
                v-model="pulse.subprotocols"
                class="dropzone"
                :group="{ name: 'order' }"
                :ghost-class="'ghost'"
                :emptyInsertThreshold="40"
                :disabled="isNestingDisabled"
                @change="handleProtocolLoop($event, idx)"
                @start="isDragging = true"
                @end="isDragging = false"
              >
                <div
                  v-for="(nestedPulse, nestedIdx) in pulse.subprotocols"
                  :key="nestedIdx"
                  :style="'position: relative;'"
                  @dblclick="openModalForEdit(nestedPulse.type, idx, nestedIdx)"
                  @mouseenter="onPulseEnter(idx, nestedIdx)"
                  @mouseleave="onPulseLeave"
                >
                  <img :src="require(`@/assets/img/${nestedPulse.type}.png`)" :style="'margin-top: 4px;'" />
                </div>
              </draggable>
            </div>
          </draggable>
        </div>
      </div>
    </div>
    <div v-if="modalType !== null" class="modal-container">
      <StimulationStudioWaveformSettingModal
        :pulseType="modalType"
        :modalOpenForEdit="modalOpenForEdit"
        :selectedPulseSettings="selectedPulseSettings"
        :currentColor="selectedColor"
        @close="onModalClose"
      />
    </div>
    <div v-if="openDelayModal" class="modal-container delay-container">
      <StimulationStudioInputModal
        :modalOpenForEdit="modalOpenForEdit"
        :currentUnit="currentDelayUnit"
        :currentInput="currentInput"
        :currentColor="selectedColor"
        @input-close="onModalClose"
      />
    </div>
    <div v-if="openRepeatModal" class="modal-container repeat-container">
      <StimulationStudioInputModal
        :modalOpenForEdit="modalOpenForEdit"
        :currentInput="currentInput"
        :inputLabel="'Number of Loops:'"
        :includeUnits="false"
        :modalTitle="'Repeat Setup'"
        @input-close="closeRepeatModal"
      />
    </div>
  </div>
</template>
<script>
import StimulationStudioWaveformSettingModal from "@/components/stimulation/StimulationStudioWaveformSettingModal.vue";
import StimulationStudioInputModal from "@/components/stimulation/StimulationStudioInputModal.vue";
import SmallDropDown from "@/components/basic-widgets/SmallDropDown.vue";
import { generateRandomColor } from "@/js-utils/WaveformDataFormatter";

import draggable from "vuedraggable";
import { mapState, mapActions, mapMutations } from "vuex";
/**
 * @vue-data {Array} iconType - The source for the draggable pulse tiles
 * @vue-data {Array} isDragging - Boolean to determine if user is currently dragging a tile in the scrollable window
 * @vue-data {Array} timeUnitsArray - Available units of time for drop down in settings panel
 * @vue-data {Object} selectedPulseSettings - This is the saved setting for a pulse that changes when a user opens a modal to edit a pulse
 * @vue-data {Array} protocolOrder -  This is the complete order of pulses/delays/repeats in the entire new protocol
 * @vue-data {String} modalType - Tracks which modal should open based on pulse type
 * @vue-data {String} settingType - This is the stimulation type that user selects from drop down in settings panel
 * @vue-data {Int} dblClickPulseIdx - Index of selected pulse to edit in order to save new settings to correct pulse
 * @vue-data {String} openDelayModal - Tracks which modal should open based on if it is a repeat or delay
 * @vue-data {String} currentInput - Saved input for a delay block that changes depending on which delay block is opened for edit
 * @vue-data {Boolean} cloned - Determines if a placed tile in protocol order is new and needs a modal to open appear to set settings or just an order rearrangement of existing tiles
 * @vue-data {Int} newClonedIdx - If tile placed in protocol order is new, this index allows settings to be saved to correct index in order
 * @vue-data {Boolean} modalOpenForEdit - Determines if existing modal inputs should appear in modal for a reedit or if it's a new delay block with blank settings
 * @vue-data {Int} timeUnitsIdx - Index for selected unit in dropdown, used to reset dropdown when editor is reset
 * @vue-data {Boolean} disableDropdown - Determines if the dropdown is disabled or not dependent on the stop stim setting selected
 * @vue-event {Event} checkType - Checks if tile placed is new or existing and opens corresponding modal for settings or commits change in protocol order to state
 * @vue-event {Event} onModalClose - Handles settings when modal is closed dependent on which button the user selects and which modal type is open, commits change to state
 * @vue-event {Event} openModalForEdit - Assigns selected pulse settings to modal for reedit and saves current selected index
 * @vue-event {Event} handleTimeUnit - Tracks which unit of time has been selected from dropdown in settings panel
 * @vue-event {Event} clone - Creates blank properties for new pulse placed in protocol order so that each pulse has unique properties and is not affected by one another, a side effect from VueDraggable
 */

export default {
  name: "StimulationStudioDragAndDropPanel",
  components: {
    draggable,
    StimulationStudioWaveformSettingModal,
    StimulationStudioInputModal,
    SmallDropDown,
  },
  props: {
    disableEdits: { type: Boolean, default: false },
  },
  data() {
    return {
      iconTypes: ["Monophasic", "Biphasic", "Delay"],
      timeUnitsArray: ["milliseconds", "seconds", "minutes", "hours"],
      selectedPulseSettings: {},
      protocolOrder: [],
      modalType: null,
      settingType: "Current",
      dblClickPulseIdx: null,
      openDelayModal: false,
      currentInput: null,
      currentDelayUnit: "milliseconds",
      cloned: false,
      newClonedIdx: null,
      modalOpenForEdit: false,
      timeUnitsIdx: 0,
      disableDropdown: false,
      isDragging: false,
      selectedColor: null,
      includeInputUnits: true,
      openRepeatModal: false,
      dblClickPulseNestedIdx: null,
    };
  },
  computed: {
    ...mapState("stimulation", {
      timeUnit: (state) => state.protocolEditor.timeUnit,
      runUntilStopped: (state) => state.protocolEditor.runUntilStopped,
      detailedSubprotocols: (state) => state.protocolEditor.detailedSubprotocols,
    }),
    isNestingDisabled: function () {
      // disable nesting if the dragged pulse is a nested loop already to prevent deep nesting
      // OR a new pulse is being placed
      const selectedPulse = this.protocolOrder[this.isDragging];

      return (
        (Number.isInteger(this.isDragging) && selectedPulse && selectedPulse.type === "loop") || this.cloned
      );
    },
  },
  watch: {
    isDragging: function () {
      // reset so old position/idx isn't highlighted once moved
      this.onPulseMouseleave();
    },
    detailedSubprotocols: function () {
      this.protocolOrder = JSON.parse(
        JSON.stringify(
          this.detailedSubprotocols.map((protocol) =>
            protocol.type !== "loop"
              ? {
                  ...protocol,
                  subprotocols: [],
                }
              : protocol
          )
        )
      );
    },
    timeUnit: function () {
      this.timeUnitsIdx = this.timeUnitsArray.indexOf(this.timeUnit);
    },
    runUntilStopped: function () {
      this.disableDropdown = !this.runUntilStopped;
    },
  },
  methods: {
    ...mapActions("stimulation", ["handleProtocolOrder", "onPulseMouseenter"]),
    ...mapMutations("stimulation", ["setTimeUnit", "onPulseMouseleave"]),

    checkType(e) {
      if (e.added && this.cloned) {
        const { element, newIndex } = e.added;
        this.newClonedIdx = newIndex;
        this.selectedPulseSettings = element.pulseSettings;
        this.selectedColor = element.color;
        if (["Monophasic", "Biphasic"].includes(element.type)) this.modalType = element.type;
        else if (element.type === "Delay") this.openDelayModal = true;
      } else if (e.removed) {
        this.selectedPulseSettings = e.removed.element;
      }

      if ((e.added && !this.cloned) || e.moved || e.removed) {
        // if the first index of a loop gets removed from the loop, it gets added here with subprotocols, need to remove
        this.handleProtocolOrder(this.protocolOrder);
      }
      // reset
      this.cloned = false;
    },
    onModalClose(button, pulseSettings, selectedColor) {
      this.modalType = null;
      this.currentInput = null;
      this.currentDelayUnit = "milliseconds";
      this.selectedColor = null;

      if (this.newClonedIdx !== null) {
        this.handleNewSettings(button, pulseSettings, selectedColor);
      } else if (isNaN(this.dblClickPulseNestedIdx)) {
        this.handleEditedSettings(button, pulseSettings, selectedColor);
      } else {
        this.handleNestedSettings(button, pulseSettings, selectedColor);
      }

      // dispatch vuex state changes
      this.handleProtocolOrder(this.protocolOrder);
    },
    startDragging({ oldIndex }) {
      this.isDragging = oldIndex;
    },
    handleNewSettings(button, pulseSettings, selectedColor) {
      const newPulse = this.protocolOrder[this.newClonedIdx];

      switch (button) {
        case "Save":
          newPulse.color = selectedColor;
          Object.assign(newPulse.pulseSettings, pulseSettings);
          break;
        case "Cancel":
          this.protocolOrder.splice(this.newClonedIdx, 1);
      }

      this.newClonedIdx = null;
      this.openDelayModal = false;
    },
    handleEditedSettings(button, pulseSettings, selectedColor) {
      const editedPulse = this.protocolOrder[this.dblClickPulseIdx];
      const duplicatePulse = JSON.parse(JSON.stringify(editedPulse));

      // change color and insert after original pulse
      const previousHue = this.getPulseHue(this.dblClickPulseIdx);
      const nextHue =
        this.dblClickPulseIdx < this.protocolOrder.length - 1
          ? this.getPulseHue(this.dblClickPulseIdx + 1)
          : undefined;

      switch (button) {
        case "Save":
          Object.assign(editedPulse.pulseSettings, pulseSettings);
          editedPulse.color = selectedColor;
          break;
        case "Duplicate":
          duplicatePulse.color = generateRandomColor(true, previousHue, nextHue);
          this.protocolOrder.splice(this.dblClickPulseIdx + 1, 0, duplicatePulse);
          break;
        case "Delete":
          this.protocolOrder.splice(this.dblClickPulseIdx, 1);
          break;
      }

      this.dblClickPulseIdx = null;
      this.openDelayModal = false;
      this.modalOpenForEdit = false;
    },
    handleNestedSettings(button, pulseSettings, selectedColor) {
      const editedPulse = this.protocolOrder[this.dblClickPulseIdx];
      const { subprotocols } = editedPulse;
      // needs to not edit original pulse, editedPulse does
      const editedNestedPulse = subprotocols[this.dblClickPulseNestedIdx];
      const editedNestedPulseCopy = JSON.parse(JSON.stringify(editedNestedPulse));
      const numSubprotocols = subprotocols.length;
      const previousHue = this.getPulseHue(this.dblClickPulseIdx, this.dblClickPulseNestedIdx);
      // intentionally set to undefined if neither of the following conditionals are met
      let nextHue;

      switch (button) {
        case "Save":
          Object.assign(editedNestedPulse.pulseSettings, pulseSettings);
          editedNestedPulse.color = selectedColor;
          break;
        case "Duplicate":
          // next conditional checks if pulse is not last in loop
          if (numSubprotocols - 1 > this.dblClickPulseNestedIdx)
            nextHue = this.getPulseHue(this.dblClickPulseIdx, this.dblClickPulseNestedIdx + 1);
          // else take next pulse outside of loop to prevent duplciate colors in a row
          else if (
            numSubprotocols - 1 == this.dblClickPulseNestedIdx &&
            this.dblClickPulseIdx < this.protocolOrder.length - 1
          )
            nextHue = this.getPulseHue(this.dblClickPulseIdx + 1);
          // else no need to consider next in order

          editedNestedPulseCopy.color = generateRandomColor(true, previousHue, nextHue);
          editedPulse.subprotocols.splice(this.dblClickPulseNestedIdx + 1, 0, editedNestedPulseCopy);
          break;
        case "Delete":
          editedPulse.subprotocols.splice(this.dblClickPulseNestedIdx, 1);
          break;
      }

      this.dblClickPulseNestedIdx = null;
      this.openDelayModal = false;
      this.modalOpenForEdit = false;
    },
    closeRepeatModal(button, value) {
      this.openRepeatModal = false;
      this.currentInput = null;
      // create loop object to replace at index in protocol order
      const loopPulse = {
        type: "loop",
        numInterations: value,
        subprotocols: [this.protocolOrder[this.dblClickPulseIdx], this.selectedPulseSettings],
      };

      switch (button) {
        case "Save":
          if (this.modalOpenForEdit) {
            this.protocolOrder[this.dblClickPulseIdx].numInterations = value;
          } else {
            this.protocolOrder.splice(this.dblClickPulseIdx, 1, loopPulse);
          }
          break;
        case "Duplicate":
          this.protocolOrder.splice(this.dblClickPulseIdx, 0, this.protocolOrder[this.dblClickPulseIdx]);
          break;
        case "Delete":
          this.protocolOrder.splice(this.dblClickPulseIdx, 1);
          break;
        case "Cancel":
          if (!this.modalOpenForEdit) {
            this.protocolOrder.splice(this.dblClickPulseIdx + 1, 0, this.selectedPulseSettings);
          }
      }

      this.handleProtocolOrder(this.protocolOrder);
      this.modalOpenForEdit = false;
      this.dblClickPulseIdx = null;
    },
    openModalForEdit(type, idx, nestedIdx) {
      const pulse =
        nestedIdx >= 0 ? this.protocolOrder[idx].subprotocols[nestedIdx] : this.protocolOrder[idx];

      this.dblClickPulseIdx = idx;
      this.dblClickPulseNestedIdx = nestedIdx;
      this.modalOpenForEdit = true;
      this.selectedPulseSettings = pulse.pulseSettings;
      this.selectedColor = pulse.color;

      if (["Monophasic", "Biphasic"].includes(type)) {
        this.modalType = type;
      } else if (type === "Delay") {
        const { duration, unit } = this.selectedPulseSettings;
        this.currentInput = duration.toString();
        this.currentDelayUnit = unit.toString();
        this.openDelayModal = true;
      }
    },
    onPulseEnter(idx, nestedIdx) {
      // if tile is being dragged, the pulse underneath the dragged tile will highlight even though the user is dragging a different tile
      // 0 index is considered falsy
      if (!this.isDragging && this.isDragging !== 0) this.onPulseMouseenter({ idx, nestedIdx });
    },
    onPulseLeave() {
      this.onPulseMouseleave();
    },
    handleTimeUnit(idx) {
      const unit = this.timeUnitsArray[idx];
      this.timeUnitsIdx = idx;
      this.setTimeUnit(unit);
      this.handleProtocolOrder(this.protocolOrder);
    },
    getPulseHue(idx, nestedIdx) {
      // duplicated pulses are not always in last index
      const pulseIdx = idx ? idx : this.protocolOrder.length - 1;
      const selectedPulse = this.protocolOrder[pulseIdx];
      const { subprotocols } = selectedPulse;

      const lastPulseHsla =
        selectedPulse.type !== "loop"
          ? selectedPulse.color
          : subprotocols[nestedIdx >= 0 ? nestedIdx : subprotocols.length - 1].color;

      return lastPulseHsla.split("(")[1].split(",")[0];
    },
    getBorderStyle(type) {
      if (type.type === "loop") {
        const consistentColorToUse = type.subprotocols[0].color;
        return "border: 2px solid " + consistentColorToUse;
      }
    },
    clone(type) {
      this.cloned = true;

      const randomColor =
        this.protocolOrder.length > 0
          ? generateRandomColor(true, this.getPulseHue())
          : generateRandomColor(true);

      this.selectedColor = randomColor;

      let typeSpecificSettings =
        type === "Delay"
          ? { duration: "", unit: "milliseconds" }
          : // for both monophasic and biphasic
            {
              frequency: "",
              totalActiveDuration: {
                duration: "",
                unit: "milliseconds",
              },
              numCycles: 0,
              postphaseInterval: "",
              phaseOneDuration: "",
              phaseOneCharge: "",
            };

      if (type === "Biphasic")
        typeSpecificSettings = {
          ...typeSpecificSettings,
          interphaseInterval: "",
          phaseTwoCharge: "",
          phaseTwoDuration: "",
        };

      return {
        type,
        color: randomColor,
        pulseSettings: typeSpecificSettings,
        subprotocols: [],
      };
    },
    openRepeatModalForEdit(number, idx) {
      this.dblClickPulseIdx = idx;
      this.currentInput = number.toString();
      this.modalOpenForEdit = true;
      this.openRepeatModal = true;
    },
    handleProtocolLoop(e, idx) {
      if (e.added) {
        if (this.protocolOrder[idx].type !== "loop") {
          this.dblClickPulseIdx = idx;
          this.openRepeatModal = true;
        } else {
          this.handleProtocolOrder(this.protocolOrder);
        }
      } else if (e.moved) {
        this.handleProtocolOrder(this.protocolOrder);
      } else if (e.removed) {
        const { subprotocols } = this.protocolOrder[idx];
        const subprotocolsLeft = subprotocols.length;

        // if last nested subprotocol is removed from loop so there is only one left,
        // then replace loop object with last subprotocol object
        if (subprotocolsLeft === 1) {
          this.protocolOrder.splice(idx, 1, subprotocols[0]);
        }

        this.handleProtocolOrder(this.protocolOrder);
      }
    },
  },
};
</script>
<style scoped>
.div__sidebar-block {
  z-index: 999;
  background: black;
  position: absolute;
  opacity: 0.6;
  height: 885px;
  width: 300px;
  left: 1329px;
  top: 0px;
  left: 0px;
}

.div__DragAndDdrop-panel {
  background: rgb(17, 17, 17);
  position: absolute;
  width: 300px;
  height: 885px;
  bottom: 0;
  left: 1329px;
  display: flex;
  justify-content: center;
  justify-self: flex-end;
}

.div__repeat-container {
  display: flex;
  align-items: center;
  padding-left: 1px;
}

.span__repeat-label {
  font-size: 12px;
  font-weight: bold;
  position: relative;
  font-family: Muli;
  color: rgb(17, 17, 17);
}

.div__repeat-label-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
}

.img__icon-container {
  cursor: pointer;
  height: 93px;
  width: 92px;
}

img {
  height: 93px;
  width: 92px;
  cursor: pointer;
}

.ghost {
  padding: 0 7px;
}

.modal-container {
  left: 22%;
  position: absolute;
}

.dropdown-container {
  position: absolute;
  z-index: 2;
  top: 412px;
  left: 1184px;
}

.dragArea {
  height: 98px;
  display: flex;
  padding-top: 4px;
}

.div__circle {
  width: 30px;
  height: 30px;
  border: 1px solid #222;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #b7b7b7;
  cursor: pointer;
}

.draggable_tile_container {
  display: grid;
  width: 80%;
  grid-template-columns: 50% 50%;
  grid-template-rows: 15% 15% 70%;
  justify-items: center;
  align-items: center;
  margin-top: 80px;
}

.modal_overlay {
  width: 1629px;
  height: 885px;
  position: absolute;
  top: 0;
  background: rgb(0, 0, 0);
  z-index: 5;
  opacity: 0.6;
}

.div__scroll-container {
  position: absolute;
  top: 460px;
  width: 1301px;
  height: 107px;
  right: 312px;
  background: rgb(17, 17, 17);
  overflow-x: scroll;
  overflow-y: hidden;
  z-index: 1;
  white-space: nowrap;
}

::-webkit-scrollbar {
  -webkit-appearance: none;
  height: 8px;
  overflow: visible;
}

::-webkit-scrollbar-thumb {
  background-color: #2f2f2f;
  overflow: visible;
}

::-webkit-scrollbar-track {
  background-color: #1c1c1c;
  overflow: visible;
}

.span__stimulationstudio-drag-drop-header-label {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  position: absolute;
  padding-top: 25px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-size: 19px;
  color: rgb(255, 255, 255);
  text-align: center;
}

.canvas__stimulationstudio-header-separator {
  transform: rotate(0deg);
  pointer-events: all;
  position: absolute;
  width: 272px;
  height: 2px;
  top: 65px;
  visibility: visible;
  background-color: #3f3f3f;
  opacity: 0.5;
}

.dropzone {
  visibility: visible;
  height: 101px;
  display: flex;
}

.delay-container,
.repeat-container {
  top: 15%;
}
</style>
