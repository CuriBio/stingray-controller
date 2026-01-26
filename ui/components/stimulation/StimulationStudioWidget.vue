<template>
  <div class="div__simulationstudio-backdrop">
    <span
      v-for="columnIndex in numCols"
      :key="'column_' + columnIndex"
      :style="columnOffset(columnIndex - 1)"
      class="span__stimulationstudio-column-index"
    >
      <label
        :id="'column_' + columnIndex"
        @click.exact="onSelect(columnIndex, columnValues)"
        @click.shift.exact="onShiftClick(columnIndex, columnValues)"
        @mouseenter="onEnterHover(columnIndex, columnValues)"
        @mouseleave="onLeaveHover(columnIndex, columnValues)"
        >{{ columnIndex }}</label
      >
    </span>
    <span
      v-for="(v, i) in Object.keys(rowValues)"
      :key="'row_' + v"
      :style="rowOffset(i)"
      class="span__stimulationstudio-row-index"
    >
      <label
        :id="'row_' + i"
        @click.exact="onSelect(v, rowValues)"
        @click.shift.exact="onShiftClick(v, rowValues)"
        @mouseenter="onEnterHover(v, rowValues)"
        @mouseleave="onLeaveHover(v, rowValues)"
      >
        {{ v }}</label
      >
    </span>
    <span
      class="span__stimulationstudio-toggle-plus-minus-icon"
      @click.exact="onSelectCancelAll(allSelectOrCancel)"
      @mouseenter="onPlusMinusEnterHover(allSelectOrCancel)"
      @mouseleave="onPlusMinusLeaveHover(allSelectOrCancel)"
    >
      <FontAwesomeIcon v-show="allSelectOrCancel" id="plus" :icon="['fa', 'plus-circle']" />
      <FontAwesomeIcon v-show="!allSelectOrCancel" id="minus" :icon="['fa', 'minus-circle']" />
    </span>
    <div v-for="wellIndex in Array(numberOfWells).keys()" :key="wellIndex">
      <StimulationStudioPlateWell
        :id="'plate_' + wellIndex"
        :class="hoverColor[wellIndex]"
        :protocolType="getProtocolLetter(wellIndex)"
        :stroke="hoverColor[wellIndex]"
        :strokeWdth="strokeWidth[wellIndex]"
        :protocolFill="getProtocolColor(wellIndex)"
        :index="wellIndex"
        :disable="assignedOpenCircuits.includes(wellIndex)"
        :display="disable"
        @enter-well="onWellEnter(wellIndex)"
        @leave-well="onWellLeave(wellIndex)"
        @click-exact="basicSelect(wellIndex)"
        @click-shift-exact="basicShiftSelect(wellIndex)"
      />
    </div>
    <div v-if="disable" class="div__simulationstudio-disable-overlay" :style="'opacity: 0;'" />
    <div
      v-if="shortCircuitErrorFound"
      v-b-popover.hover.bottom="'Stimulation lid must be replaced before running a stimulation'"
      title="Error"
      class="div__simulationstudio-disable-overlay"
      :style="'opacity: 0.7;'"
    >
      <div class="div__disabled-overlay-text">Disabled</div>
    </div>
  </div>
</template>
<script>
import StimulationStudioPlateWell from "@/components/stimulation/StimulationStudioPlateWell.vue";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";

import { library } from "@fortawesome/fontawesome-svg-core";
import { faPlusCircle, faMinusCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { mapState } from "vuex";
import Vue from "vue";
import { VBPopover } from "bootstrap-vue";

Vue.directive("b-popover", VBPopover);
library.add(faMinusCircle);
library.add(faPlusCircle);

const NUM_ROWS = 8;
const NUM_COLS = 12;

const NO_STROKE_WIDTH = 0;
const HOVER_STROKE_WIDTH = 2;
const SELECTED_STROKE_WIDTH = 4;
const HOVER_COLOR = "#ECECED";
const SELECTED_COLOR = "#FFFFFF";

export default {
  name: "StimulationStudioWidget",
  components: { FontAwesomeIcon, StimulationStudioPlateWell },
  props: {
    numberOfWells: { type: Number, default: NUM_COLS * NUM_ROWS },
    disable: { type: Boolean, default: false },
  },
  data() {
    return {
      numRows: NUM_ROWS,
      numCols: NUM_COLS,
      rowValues: {
        A: Array.from({ length: NUM_COLS }, (_, i) => 0 + i * NUM_ROWS),
        B: Array.from({ length: NUM_COLS }, (_, i) => 1 + i * NUM_ROWS),
        C: Array.from({ length: NUM_COLS }, (_, i) => 2 + i * NUM_ROWS),
        D: Array.from({ length: NUM_COLS }, (_, i) => 3 + i * NUM_ROWS),
        E: Array.from({ length: NUM_COLS }, (_, i) => 4 + i * NUM_ROWS),
        F: Array.from({ length: NUM_COLS }, (_, i) => 5 + i * NUM_ROWS),
        G: Array.from({ length: NUM_COLS }, (_, i) => 6 + i * NUM_ROWS),
        H: Array.from({ length: NUM_COLS }, (_, i) => 7 + i * NUM_ROWS),
      },
      columnValues: {
        1: Array.from({ length: NUM_ROWS }, (_, i) => 0 + i),
        2: Array.from({ length: NUM_ROWS }, (_, i) => 8 + i),
        3: Array.from({ length: NUM_ROWS }, (_, i) => 16 + i),
        4: Array.from({ length: NUM_ROWS }, (_, i) => 24 + i),
        5: Array.from({ length: NUM_ROWS }, (_, i) => 32 + i),
        6: Array.from({ length: NUM_ROWS }, (_, i) => 40 + i),
        7: Array.from({ length: NUM_ROWS }, (_, i) => 48 + i),
        8: Array.from({ length: NUM_ROWS }, (_, i) => 56 + i),
        9: Array.from({ length: NUM_ROWS }, (_, i) => 64 + i),
        10: Array.from({ length: NUM_ROWS }, (_, i) => 72 + i),
        11: Array.from({ length: NUM_ROWS }, (_, i) => 80 + i),
        12: Array.from({ length: NUM_ROWS }, (_, i) => 88 + i),
      },
      allSelectOrCancel: false,
      hover: new Array(this.numberOfWells).fill(false),
      allSelect: new Array(this.numberOfWells).fill(false),
      hoverColor: new Array(this.numberOfWells).fill(HOVER_COLOR),
      strokeWidth: new Array(this.numberOfWells).fill(NO_STROKE_WIDTH),
    };
  },
  computed: {
    ...mapState("stimulation", [
      "protocolAssignments",
      "stimStatus",
      "selectedWells",
      "stimulatorCircuitStatuses",
    ]),
    shortCircuitErrorFound: function () {
      return this.stimStatus === STIM_STATUS.SHORT_CIRCUIT_ERROR;
    },
    assignedOpenCircuits: function () {
      // filter for matching indices
      return this.stimulatorCircuitStatuses.filter((well) =>
        Object.keys(this.protocolAssignments).includes(well.toString())
      );
    },
  },
  watch: {
    allSelect: function () {
      this.$store.dispatch("stimulation/handleSelectedWells", this.allSelect);
    },
    selectedWells: function (newWells, previousWells) {
      // second conditional prevents infinite looping of constantly reassigning to 0
      if (newWells.length === 0 && previousWells.length !== 0) {
        this.allSelect = new Array(this.numberOfWells).fill(false);
        this.strokeWidth = new Array(this.numberOfWells).fill(NO_STROKE_WIDTH);
        if (!this.allSelectOrCancel) this.allSelectOrCancel = true;
      }
    },
  },
  created() {
    this.strokeWidth.splice(0, this.strokeWidth.length);
    this.checkStrokeWidth();
    const allEqual = (arr) => arr.every((v) => v === true); // verify in the pre-select all via a const allEqual function.
    this.allSelectOrCancel = allEqual(this.allSelect) ? false : true; // if pre-select has all wells is true, then toggle from (+) to (-) icon.
  },
  methods: {
    rowOffset: function (idx) {
      const top = 31 + 34 * idx;
      return `top: ${top}px;`;
    },
    columnOffset: function (idx) {
      const left = 26 + 34 * idx;
      return `left: ${left}px;`;
    },
    onSelectCancelAll(state) {
      this.allSelectOrCancel = !state;
      this.allSelect = new Array(this.numberOfWells).fill(state);
      this.$store.dispatch("stimulation/handleSelectedWells", this.allSelect);
      this.strokeWidth.splice(0, this.strokeWidth.length);
      this.checkStrokeWidth();
    },

    onPlusMinusEnterHover() {
      this.strokeWidth.splice(0, this.strokeWidth.length);
      for (let j = 0; j < this.allSelect.length; j++) {
        this.strokeWidth[j] = !this.allSelect[j] ? HOVER_STROKE_WIDTH : SELECTED_STROKE_WIDTH;
      }
    },

    onPlusMinusLeaveHover() {
      this.strokeWidth.splice(0, this.strokeWidth.length);
      this.checkStrokeWidth();
    },

    basicSelect(value) {
      this.allSelect = new Array(this.numberOfWells).fill(false);
      this.allSelect[value] = true;
      this.strokeWidth[value] = SELECTED_STROKE_WIDTH;
      if (!this.allSelectOrCancel) this.allSelectOrCancel = true;
      this.onWellEnter(value);
    },

    basicShiftSelect(value) {
      const allEqual = (arr) => arr.every((v) => v === true);
      this.allSelect[value] = !this.allSelect[value];
      this.strokeWidth[value] = SELECTED_STROKE_WIDTH;
      if (allEqual(this.allSelect)) this.allSelectOrCancel = false;
      else this.allSelectOrCancel = true;
      this.$store.dispatch("stimulation/handleSelectedWells", this.allSelect);
      this.onWellEnter(value);
    },

    onWellEnter(value) {
      this.hover[value] = true;
      this.hoverColor[value] = "#ececed";
      this.strokeWidth.splice(0, this.strokeWidth.length);
      this.checkStrokeWidth();
      this.strokeWidth[value] = this.allSelect[value] ? SELECTED_STROKE_WIDTH : HOVER_STROKE_WIDTH;
    },

    onWellLeave(value) {
      this.hover[value] = false;
      this.hoverColor[value] = SELECTED_COLOR;
      this.strokeWidth.splice(0, this.strokeWidth.length);
      this.checkStrokeWidth();
    },

    onSelect(val, valuesToChange) {
      this.allSelect = new Array(this.numberOfWells).fill(false);
      this.strokeWidth.splice(0, this.strokeWidth.length);
      valuesToChange[val].map((well) => (this.allSelect[well] = true));
      if (!this.allSelectOrCancel) this.allSelectOrCancel = true;
      this.checkStrokeWidth();
    },

    onEnterHover(val, valuesToChange) {
      const newList = JSON.parse(JSON.stringify(this.strokeWidth));
      this.strokeWidth.splice(0, this.strokeWidth.length);

      valuesToChange[val].map(
        (well) => (newList[well] = newList[well] == NO_STROKE_WIDTH ? HOVER_STROKE_WIDTH : newList[well])
      );
      this.strokeWidth = newList;
    },

    onLeaveHover() {
      this.strokeWidth.splice(0, this.strokeWidth.length);
      this.checkStrokeWidth();
    },

    onShiftClick(val, valuesToChange) {
      const newList = JSON.parse(JSON.stringify(this.allSelect));
      this.strokeWidth.splice(0, this.strokeWidth.length);
      const result = valuesToChange[val].map((i) => newList[i]).every((x) => x);
      valuesToChange[val].map((well) => {
        newList[well] = !result;
      });

      this.allSelect = newList;
      const allEqual = (arr) => arr.every((v) => v === true); // verify in the pre-select all via a const allEqual function.
      this.allSelectOrCancel = allEqual(this.allSelect) ? false : true; // if pre-select has all wells is true, then toggle from (+) to (-) icon.
      this.checkStrokeWidth();
    },
    checkStrokeWidth() {
      for (let i = 0; i < this.allSelect.length; i++) {
        this.strokeWidth[i] = !this.allSelect[i] ? NO_STROKE_WIDTH : SELECTED_STROKE_WIDTH;
        this.hoverColor[i] = !this.allSelect[i] ? HOVER_COLOR : SELECTED_COLOR;
      }
    },
    getProtocolColor(index) {
      return this.protocolAssignments[index] ? this.protocolAssignments[index].color : "#B7B7B7";
    },

    getProtocolLetter(index) {
      return this.protocolAssignments[index] ? this.protocolAssignments[index].letter : "";
    },
  },
};
</script>
<style scoped>
.div__simulationstudio-backdrop {
  box-sizing: border-box;
  padding: 0px;
  margin: 0px;
  background: rgb(28, 28, 28);
  position: absolute;
  width: 452px;
  height: 308px;
  visibility: visible;
  border-radius: 10px;
  box-shadow: rgba(0, 0, 0, 0.7) 0px 0px 10px 0px;
  pointer-events: all;
  z-index: 2;
}
.span__simulationstudio-plus-icon {
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 20px;
  height: 20px;
  line-height: 20px;
  top: 5px;
  left: 5px;
  font-size: 20px;
  color: rgb(183, 183, 183);
}
.span__stimulationstudio-row-index {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  position: absolute;
  width: 22px;
  height: 25px;
  left: 8px;
  margin-top: 2px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
  text-align: left;
}
.span__stimulationstudio-column-index {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  position: absolute;
  width: 53px;
  height: 27px;
  top: 3px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(183, 183, 183);
  text-align: center;
}
.span__stimulationstudio-column-index label:hover,
.span__stimulationstudio-row-index label:hover {
  color: #ececed;
  cursor: pointer;
}
.span__stimulationstudio-toggle-plus-minus-icon {
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 20px;
  height: 20px;
  line-height: 20px;
  top: 9px;
  left: 9px;
  font-size: 20px;
  color: rgb(183, 183, 183);
}
.span__stimulationstudio-toggle-plus-minus-icon:hover {
  color: #ffffff;
  cursor: pointer;
}
.div__simulationstudio-disable-overlay {
  height: 308px;
  width: 452px;
  z-index: 3;
  border-radius: 10px;
  background-color: black;
  display: flex;
  align-items: center;
  justify-content: center;
}
.div__disabled-overlay-text {
  color: #b7b7b7;
  font-family: Muli;
  font-size: 70px;
  font-style: italic;
  opacity: 0.5;
  font-weight: 500;
}
</style>
