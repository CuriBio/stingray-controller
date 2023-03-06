<template>
  <div class="div__simulationstudio-backdrop">
    <span
      v-for="columnIndex in 6"
      :key="'column_' + columnIndex"
      :style="columnComputedOffsets[columnIndex - 1]"
      class="span__stimulationstudio-column-index"
    >
      <label
        :id="'column_' + columnIndex"
        @click.exact="onSelect(columnIndex, columnValues)"
        @click.shift.exact="onShiftClick(columnIndex, columnValues)"
        @mouseenter="onEnterHover(columnIndex, columnValues)"
        @mouseleave="onLeaveHover(columnIndex, columnValues)"
        >0{{ columnIndex }}</label
      >
    </span>
    <span
      v-for="(v, i) in Object.keys(rowValues)"
      :key="'row_' + v"
      :style="rowComputedOffsets[i]"
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
        @enter-well="onWellenter(wellIndex)"
        @leave-well="onWellleave(wellIndex)"
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
import StimulationStudioPlateWell from "@/components/basic-widgets/StimulationStudioPlateWell.vue";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faPlusCircle, faMinusCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { mapState } from "vuex";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import Vue from "vue";
import { VBPopover } from "bootstrap-vue";

Vue.directive("b-popover", VBPopover);
library.add(faMinusCircle);
library.add(faPlusCircle);

const noStrokeWidth = 0;
const hoverStrokeWidth = 2;
const selectedStrokeWidth = 4;
const hoverColor = "#ececed";
const selectedColor = "#FFFFFF";

export default {
  name: "StimulationStudioWidget",
  components: { FontAwesomeIcon, StimulationStudioPlateWell },
  props: {
    numberOfWells: { type: Number, default: 24 },
    disable: { type: Boolean, default: false },
  },
  data() {
    return {
      rowValues: {
        A: [0, 4, 8, 12, 16, 20],
        B: [1, 5, 9, 13, 17, 21],
        C: [2, 6, 10, 14, 18, 22],
        D: [3, 7, 11, 15, 19, 23],
      },
      columnValues: {
        1: [0, 1, 2, 3],
        2: [4, 5, 6, 7],
        3: [8, 9, 10, 11],
        4: [12, 13, 14, 15],
        5: [16, 17, 18, 19],
        6: [20, 21, 22, 23],
      },
      allSelectOrCancel: false,
      hover: new Array(this.numberOfWells).fill(false),
      allSelect: new Array(this.numberOfWells).fill(false),
      hoverColor: new Array(this.numberOfWells).fill(hoverColor),
      strokeWidth: new Array(this.numberOfWells).fill(noStrokeWidth),
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
    rowComputedOffsets: function () {
      return ["41", "103", "165", "224"].map((v) => "top:" + v + "px;");
    },
    columnComputedOffsets: function () {
      return ["39", "101", "164", "225", "287", "349"].map((v) => "left:" + v + "px;");
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
        this.strokeWidth = new Array(this.numberOfWells).fill(noStrokeWidth);
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
        this.strokeWidth[j] = !this.allSelect[j] ? hoverStrokeWidth : selectedStrokeWidth;
      }
    },

    onPlusMinusLeaveHover() {
      this.strokeWidth.splice(0, this.strokeWidth.length);
      this.checkStrokeWidth();
    },

    basicSelect(value) {
      this.allSelect = new Array(this.numberOfWells).fill(false);
      this.allSelect[value] = true;
      this.strokeWidth[value] = selectedStrokeWidth;
      if (!this.allSelectOrCancel) this.allSelectOrCancel = true;
      this.onWellenter(value);
    },

    basicShiftSelect(value) {
      const allEqual = (arr) => arr.every((v) => v === true);
      this.allSelect[value] = !this.allSelect[value];
      this.strokeWidth[value] = selectedStrokeWidth;
      if (allEqual(this.allSelect)) this.allSelectOrCancel = false;
      else this.allSelectOrCancel = true;
      this.$store.dispatch("stimulation/handleSelectedWells", this.allSelect);
      this.onWellenter(value);
    },

    onWellenter(value) {
      this.hover[value] = true;
      this.hoverColor[value] = "#ececed";
      this.strokeWidth.splice(0, this.strokeWidth.length);
      this.checkStrokeWidth();
      this.strokeWidth[value] = this.allSelect[value] ? selectedStrokeWidth : hoverStrokeWidth;
    },

    onWellleave(value) {
      this.hover[value] = false;
      this.hoverColor[value] = selectedColor;
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
        (well) => (newList[well] = newList[well] == noStrokeWidth ? hoverStrokeWidth : newList[well])
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
        this.strokeWidth[i] = !this.allSelect[i] ? noStrokeWidth : selectedStrokeWidth;
        this.hoverColor[i] = !this.allSelect[i] ? hoverColor : selectedColor;
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
  width: 415px;
  height: 280px;
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
  height: 280px;
  width: 415px;
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
