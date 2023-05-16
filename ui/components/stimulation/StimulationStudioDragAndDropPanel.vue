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
            @start="isDragging = true"
            @end="isDragging = false"
          >
            <div
              v-for="(pulse, idx) in protocolOrder"
              :key="idx"
              :class="'div__repeat-container'"
              :style="getBorderStyle(pulse)"
            >
              <!-- Only display circular icon when nested loop, icon displays number of loops -->
              <div v-if="pulse.numRepeats" :class="'div__repeat-label-container'">
                <div class="div__circle" @dblclick="openRepeatModalForEdit(pulse.numRepeats, idx)">
                  <span :class="'span__repeat-label'">
                    {{ pulse.numRepeats }}
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
                v-model="protocolOrder"
                class="dropzone"
                style="height: 100px; display: flex"
                :group="{ name: 'order' }"
                :ghost-class="'ghost'"
                :emptyInsertThreshold="40"
                :disabled="false"
                @change="handleProtocolLoop($event, idx)"
              >
                <div
                  v-for="(nestedPulse, nestedIdx) in pulse.subprotocols"
                  :key="nestedIdx"
                  :style="'position: relative;'"
                  @dblclick="openModalForEdit(nestedPulse.type, idx, nestedIdx)"
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
        :modalTitle="'Repeat'"
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
 * @vue-data {Int} shiftClickImgIdx - Index of selected pulse to edit in order to save new settings to correct pulse
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
      shiftClickImgIdx: null,
      openDelayModal: false,
      currentInput: null,
      currentDelayUnit: "milliseconds",
      cloned: false,
      newClonedIdx: null,
      modalOpenForEdit: false, // TODO Luci, clean up state management and constant names
      timeUnitsIdx: 0,
      disableDropdown: false,
      isDragging: false,
      selectedColor: null,
      includeInputUnits: true,
      openRepeatModal: false,
    };
  },
  computed: {
    ...mapState("stimulation", {
      timeUnit: (state) => state.protocolEditor.timeUnit,
      runUntilStopped: (state) => state.protocolEditor.runUntilStopped,
      detailedSubprotocols: (state) => state.protocolEditor.detailedSubprotocols,
    }),
  },
  watch: {
    isDragging: function () {
      // reset so old position/idx isn't highlighted once moved
      this.onPulseMouseleave();
    },
    detailedSubprotocols: function () {
      this.protocolOrder = JSON.parse(JSON.stringify(this.detailedSubprotocols));
    },
    timeUnit: function () {
      this.timeUnitsIdx = this.timeUnitsArray.indexOf(this.timeUnit);
    },
    runUntilStopped: function () {
      this.disableDropdown = !this.runUntilStopped;
    },
    // protocolOrder: function() {
    //   console.log(this.protocolOrder);
    // }
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
        if (element.type === "Monophasic") this.modalType = "Monophasic";
        else if (element.type === "Biphasic") this.modalType = "Biphasic";
        else if (element.type === "Delay") this.openDelayModal = true;
      } else if (e.removed) {
        this.selectedPulseSettings = e.removed.element;
      }

      if ((e.added && !this.cloned) || e.moved || e.removed) this.handleProtocolOrder(this.protocolOrder);
      // reset
      this.cloned = false;
    },
    onModalClose(button, pulseSettings, selectedColor) {
      this.modalType = null;
      this.openDelayModal = false;
      this.modalOpenForEdit = false;
      this.currentInput = null;
      this.currentDelayUnit = "milliseconds";
      this.selectedColor = null;

      switch (button) {
        case "Save":
          if (this.newClonedIdx !== null) {
            const newPulse = this.protocolOrder[this.newClonedIdx];
            newPulse.pulseSettings = pulseSettings;
            newPulse.color = selectedColor;
            Object.assign(this.protocolOrder[this.newClonedIdx], newPulse);
          }
          if (this.shiftClickImgIdx !== null) {
            const editedPulse = this.protocolOrder[this.shiftClickImgIdx];

            Object.assign(editedPulse.pulseSettings, pulseSettings);
            Object.assign(this.protocolOrder[this.shiftClickImgIdx], editedPulse);
            editedPulse.color = selectedColor;
          }
          break;
        case "Duplicate":
          // eslint-disable-next-line no-case-declarations
          const duplicatePulse = // needs to not edit original pulse, editedPulse does
            this.shiftClickImgIdx !== null
              ? JSON.parse(JSON.stringify(this.protocolOrder[this.shiftClickImgIdx]))
              : null;

          // change color and insert after original pulse
          // eslint-disable-next-line no-case-declarations
          const previousHue = this.getPulseHue(this.shiftClickImgIdx);
          // eslint-disable-next-line no-case-declarations
          const nextHue =
            this.shiftClickImgIdx < this.protocolOrder.length - 1
              ? this.getPulseHue(this.shiftClickImgIdx + 1)
              : undefined;

          duplicatePulse.color = generateRandomColor(true, previousHue, nextHue);
          this.protocolOrder.splice(this.shiftClickImgIdx + 1, 0, duplicatePulse);
          break;
        case "Delete":
          this.protocolOrder.splice(this.shiftClickImgIdx, 1);
          break;
        case "Cancel":
          if (this.newClonedIdx !== null) {
            this.protocolOrder.splice(this.newClonedIdx, 1);
          }
      }
      this.newClonedIdx = null;
      this.shiftClickImgIdx = null;
      this.handleProtocolOrder(this.protocolOrder);
    },
    closeRepeatModal(button, value) {
      this.openRepeatModal = false;
      this.modalOpenForEdit = false;
      this.currentInput = null;

      switch (button) {
        case "Save":
          const loopPulse = {
            type: "loop",
            numRepeats: value,
            subprotocols: [this.protocolOrder[this.shiftClickImgIdx], this.selectedPulseSettings],
          };

          this.protocolOrder.splice(this.shiftClickImgIdx, 1, loopPulse);
      }
      this.handleProtocolOrder(this.protocolOrder);
      this.shiftClickImgIdx = null;
    },
    openModalForEdit(type, idx) {
      const pulse = this.protocolOrder[idx];
      this.shiftClickImgIdx = idx;
      this.modalOpenForEdit = true;
      this.selectedPulseSettings = pulse.pulseSettings;
      this.selectedColor = pulse.color;

      if (type === "Monophasic") {
        this.modalType = "Monophasic";
      } else if (type === "Biphasic") {
        this.modalType = "Biphasic";
      } else if (type === "Delay") {
        const { duration, unit } = this.selectedPulseSettings;
        this.currentInput = duration.toString();
        this.currentDelayUnit = unit.toString();
        this.openDelayModal = true;
      }
    },
    onPulseEnter(idx) {
      // if tile is being dragged, the pulse underneath the dragged tile will highlight even though the user is dragging a different tile
      if (!this.isDragging) this.onPulseMouseenter(idx);
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
    getPulseHue(idx) {
      // duplicated pulses are not always in last index
      const pulseIdx = idx ? idx : this.protocolOrder.length - 1;
      const lastPulseHsla = this.protocolOrder[pulseIdx].color;
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

      const typeSpecificSettings =
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
      };
    },
    openRepeatModalForEdit(number, idx) {
      this.shiftClickImgIdx = idx;
      this.currentInput = number;
      this.openRepeatModal = true;
      this.openModalForEdit = true;
    },
    handleProtocolLoop(e, idx) {
      console.log(idx, this.protocolOrder[idx]);
      if (e.added) {
        this.shiftClickImgIdx = idx;
        this.openRepeatModal = true;
      } else if (e.removed) {
        this.protocolOrder[idx].loops = 0;
        this.handleProtocolOrder(this.protocol_order);
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
  padding: 0 7px 7px 7px;
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
  height: 100px;
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
}

.delay-container,
.repeat-container {
  top: 15%;
}
</style>
