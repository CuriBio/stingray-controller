<template>
  <div class="div__waveform">
    <div class="div__waveform-graph" :style="div__waveformGraph_dynamicStyle" />
    <div class="div__waveform-y-axis-title">
      <span>{{ yAxisLabel }}</span>
      <StimulationStudioZoomControls :style="'padding-left: 10px'" :axis="'y-axis'" />
    </div>

    <div class="div__waveform-x-axis-title">
      <span :style="'grid-column: 1/2; align-self: center;'">{{ xAxisLabel }}</span>
      <SmallDropDown
        :style="'grid-column: 2/3;'"
        :inputHeight="9"
        :inputWidth="110"
        :optionsText="timeUnits"
        :optionsIdx="activeDurationIdx"
        :domIdSuffix="'timeUnits'"
        @selection-changed="handleTotalDurationUnitChange"
      />
      <StimulationStudioZoomControls
        :style="'grid-column: 3; align-self: center;'"
        :axis="'x-axis'"
        @zoom-out="zoomOutXAxis"
        @zoom-in="zoomInXAxis"
      />
    </div>
  </div>
</template>
<script>
import StimulationStudioZoomControls from "@/components/stimulation/StimulationStudioZoomControls.vue";
import SmallDropDown from "@/components/basic-widgets/SmallDropDown.vue";

import { mapState } from "vuex";
import { axisBottom, axisLeft, line as d3Line, select as d3Select, scaleLinear } from "d3";

/**
 * @vue-prop {String} title - Current title of the waveform
 * @vue-prop {Int} xAxisSampleLength - Current X Axis sample length
 * @vue-prop {Int} xAxisMin - Current position on X Axis
 * @vue-prop {Int} yMin - Current Minimum scale position on Y Axis
 * @vue-prop {Int} yMax - Current Maximum scale position on Y Axis
 * @vue-prop {String} yAxisLabel - Current Y Axis Label String value.
 * @vue-prop {String} xAxisLabel - Current X Axis Label String value.
 * @vue-prop {Object} dataPoints  - Currently contains the array of 2D waveform data points[[x1,y1],[x2,y2]...]
 * @vue-prop {String} lineColor   - Color of the line graph
 * @vue-prop {Object} margin       - An Object which determines a closing boundry margin
 * @vue-prop {Int} plotAreaPixelHeight - Graph height definition
 * @vue-prop {Int} plotAreaPixelWidth  - Graph widht definition
 * @vue-data {Object} theSvg             - An Object which is used to create SVG element via D3 library
 * @vue-data {Object} xAxisNode         - An Object which is used to create X Axis node
 * @vue-data {Object} xAxisScale        - An Object which is used to process the X Axis scale
 * @vue-data {Object} yAxisNode         - An Object which is used to create Y Axis node
 * @vue-data {Object} yAxisScale        - An Object which is used to process the Y Axis scale
 * @vue-data {Object} waveformLineNode  - An Object which is used to plot the line graph
 * @vue-data {Object} highlightLineNode - An Object which is used to plot the line graph to fill when hovered over
 * @vue-computed {Object}hoveredPulse       - State Object used to fill background of hovered over pulse in stim studio
 * @vue-computed {Object} div_WaveformGraph_DynamicStyle - An CSS property to hold the dynamic value
 * @vue-event {Event} xAxisMin           - A Function  is invoked when xAxisMin prop is modified
 * @vue-event {Event} xAxisSampleLength - A Function  is invoked when xAxisSampleLength prop is modified
 * @vue-event {Event} yMin                - A Function  is invoked when yMin prop is modified
 * @vue-event {Event} yMax                - A Function  is invoked when yMax prop is modified
 * @vue-event {Event} dataPoints          - A Function  is invoked when dataPoints prop is modified
 * @vue-event {Event} renderPlot          - An Important function which plots the waveform svg in realtime.
 */
export default {
  name: "StimulationStudioWaveform",
  components: { StimulationStudioZoomControls, SmallDropDown },
  props: {
    title: { type: String, default: "" },
    xAxisSampleLength: { type: Number, default: 100 },
    xAxisMin: { type: Number, default: 0 },
    yMin: { type: Number, default: 0 },
    yMax: { type: Number, default: 120 },
    yAxisLabel: { type: String, default: "Current" },
    xAxisLabel: { type: String, default: "Time" },
    dataPoints: {
      type: Array, // exactly the format D3 accepts: 2D array of [[x1,y1],[x2,y2],...]
      default: function () {
        return [];
      },
    },
    lineColor: { type: String, default: "#00c465" },
    margin: {
      type: Object,
      default: function () {
        return { top: 0, right: 20, bottom: 50, left: 60 };
      },
    },
    plotAreaPixelHeight: {
      type: Number,
      default: 352,
    },
    plotAreaPixelWidth: {
      type: Number,
      default: 1200,
    },
    repeatColors: {
      type: Array,
      default: function () {
        return [];
      },
    },
    delayBlocks: {
      type: Array,
      default: function () {
        return [];
      },
    },
  },
  data: function () {
    return {
      theSvg: null,
      xAxisNode: null,
      xAxisScale: null,
      yAxisNode: null,
      yAxisScale: null,
      waveformLineNode: null,
      highlightLineNode: null,
      frequencyOfYTicks: 5,
      timeUnits: ["milliseconds", "seconds"],
      activeDurationIdx: 0,
    };
  },
  computed: {
    ...mapState("stimulation", ["hoveredPulse", "xAxisTimeIdx"]),
    div__waveformGraph_dynamicStyle: function () {
      return { width: this.plotAreaPixelWidth + this.margin.left + this.margin.right + "px" };
    },
    frequencyOfXTicks: function () {
      return (this.plotAreaPixelWidth / 1200) * 10;
    },
  },
  watch: {
    xAxisSampleLength() {
      this.renderPlot();
    },
    yMin() {
      this.renderPlot();
    },
    yMax() {
      this.renderPlot();
    },
    dataPoints() {
      this.renderPlot();
    },
    xAxisTimeIdx() {
      // reset time unit x axis dropdown when protocol editor resets
      this.activeDurationIdx = this.xAxisTimeIdx;
    },
    plotAreaPixelWidth() {
      this.theSvg = d3Select(this.$el)
        .select(".div__waveform-graph")
        .append("svg")
        .attr("width", this.plotAreaPixelWidth + this.margin.left + this.margin.right);

      this.renderPlot();
    },
    hoveredPulse: function (newPulse) {
      this.highlightLineNode.selectAll("*").remove();
      const xAxisScale = this.xAxisScale;
      const yAxisScale = this.yAxisScale;

      if (newPulse.idx != null) {
        const startingX = this.dataPoints[newPulse.indices[0]][0];
        const endingX = this.dataPoints[newPulse.indices[1] - 1][0];

        const startingCoord = [startingX, this.yMax];
        const endingCoord = [endingX, this.yMax];
        // in order to fill entire height of graph, need minimum y to max y
        const dataToFill = [[startingX, this.yMin], startingCoord, endingCoord, [endingX, this.yMin]];
        this.highlightLineNode
          .append("path")
          .datum(dataToFill)
          .attr("fill", newPulse.color)
          .attr("stroke", newPulse.color)
          .attr("opacity", ".15")
          .attr(
            "d",
            d3Line()
              .x(function (d) {
                return xAxisScale(d[0]);
              })
              .y(function (d) {
                return yAxisScale(d[1]);
              })
          );
      }
    },
  },
  mounted: function () {
    // Eli (2/2/2020): having the svg be appended in the `data` function didn't work, so moved it to here
    this.theSvg = d3Select(this.$el)
      .select(".div__waveform-graph")
      .append("svg")
      .attr("width", this.plotAreaPixelWidth + this.margin.left + this.margin.right)
      .attr("height", this.plotAreaPixelHeight + this.margin.top + this.margin.bottom)
      .attr("style", "background-color: black; overflow: visible;")
      .append("g")
      .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")")
      .attr("id", "svgOfWaveform")
      .attr("font-family", "Muli");

    this.highlightLineNode = this.theSvg
      .append("g")
      .attr("id", "highlightLineNode")
      .attr("class", "highlightLineNode");

    this.waveformLineNode = this.theSvg
      .append("g")
      .attr("id", "waveformLineNode")
      .attr("class", "waveformPathNode");

    this.line = this.theSvg.append("g").attr("x", 40);
    // Draw black rectangles over the margins so that any excess waveform line is not visible to use
    const blockerColor = "#000000";
    const marginBlockersNode = this.theSvg.append("g").attr("id", "marginBlockersNode");
    const margin = this.margin;
    // Left Side
    marginBlockersNode
      .append("rect")
      .attr("id", "marginBlockerLeft")
      .attr("x", -margin.left)
      .attr("y", -margin.top)
      .attr("width", margin.left)
      .attr("height", 230)
      .attr("fill", blockerColor);

    // Top
    marginBlockersNode
      .append("rect")
      .attr("id", "marginBlockerTop")
      .attr("x", 0)
      .attr("y", -margin.top)
      .attr("width", this.plotAreaPixelWidth + 1)
      .attr("height", margin.top)
      .attr("fill", blockerColor);

    // Bottom
    marginBlockersNode
      .append("rect")
      .attr("id", "marginBlockerBottom")
      .attr("x", 0)
      .attr("y", this.plotAreaPixelHeight)
      .attr("width", this.plotAreaPixelWidth + 1)
      .attr("height", margin.bottom)
      .attr("fill", blockerColor);

    this.xAxisNode = this.theSvg
      .append("g")
      .attr("transform", "translate(0," + this.plotAreaPixelHeight + ")")
      .attr("id", "xAxisNode")
      .attr("stroke", "#b7b7b7")
      .attr("class", "g_Waveform-x-axis");

    this.yAxisNode = this.theSvg
      .append("g")
      .attr("id", "yAxisNode")
      .attr("stroke", "#b7b7b7")
      .attr("class", "g__waveform-y-axis");

    this.renderPlot();
  },
  methods: {
    handleTotalDurationUnitChange(idx) {
      this.activeDurationIdx = idx;
      const unitName = this.timeUnits[idx];
      this.$store.dispatch("stimulation/handleXAxisUnit", { idx, unitName });
    },
    renderPlot: function () {
      this.createXAxisScale();
      this.createYAxisScale();

      this.displayXAxis();
      this.displayYAxis();
      this.plotData();
    },
    zoomOutXAxis: function () {
      this.$emit("zoom-out");
    },
    zoomInXAxis: function () {
      this.$emit("zoom-in");
    },
    createXAxisScale: function () {
      this.xAxisScale = scaleLinear().domain([0, this.xAxisSampleLength]).range([0, this.plotAreaPixelWidth]);
    },
    createYAxisScale: function () {
      this.yAxisScale = scaleLinear().domain([this.yMin, this.yMax]).range([this.plotAreaPixelHeight, 0]);
    },
    displayXAxis: function () {
      this.xAxisNode.call(axisBottom(this.xAxisScale).ticks(this.frequencyOfXTicks));
    },
    displayYAxis: function () {
      this.yAxisNode.call(axisLeft(this.yAxisScale).ticks(this.frequencyOfYTicks));
    },
    plotData: function () {
      const dataToPlot = this.dataPoints;
      const xAxisScale = this.xAxisScale;
      const yAxisScale = this.yAxisScale;

      this.waveformLineNode.selectAll("*").remove();
      for (const assignment of this.repeatColors) {
        // repetitive, but eslint errors without a conditional inside the loop
        const startingIdx = assignment[1][0];
        const endingIdx = assignment[1][1];
        const slicedDataArray = dataToPlot.slice(startingIdx, endingIdx);

        this.waveformLineNode
          .append("path")
          .datum(slicedDataArray)
          .attr("fill", "none")
          .attr("stroke", assignment[0])
          .attr("stroke-width", 1.5)
          .attr(
            "d",
            d3Line()
              .x(function (d) {
                return xAxisScale(d[0]);
              })
              .y(function (d) {
                return yAxisScale(d[1]);
              })
          );
      }
      for (const block of this.delayBlocks) {
        // repetitive, but eslint errors without a conditional inside the loop
        if (this.delayBlocks.length !== 0 && !isNaN(block[1])) {
          const startingIdx = block[0];
          const startLine = [
            [startingIdx, this.yMin],
            [startingIdx, this.yMax],
          ];
          const endingIdx = block[1];
          const endLine = [
            [endingIdx, this.yMin],
            [endingIdx, this.yMax],
          ];

          this.waveformLineNode
            .append("path")
            .datum(startLine)
            .attr("fill", "none")
            .attr("stroke", "#ffffff")
            .attr("stroke-dasharray", "2,2")
            .attr(
              "d",
              d3Line()
                .x(function (d) {
                  return xAxisScale(d[0]);
                })
                .y(function (d) {
                  return yAxisScale(d[1]);
                })
            );
          this.waveformLineNode
            .append("path")
            .datum(endLine)
            .attr("fill", "none")
            .attr("stroke", "#ffffff")
            .attr("stroke-dasharray", "2,2")
            .attr(
              "d",
              d3Line()
                .x(function (d) {
                  return xAxisScale(d[0]);
                })
                .y(function (d) {
                  return yAxisScale(d[1]);
                })
            );
        }
      }
    },
  },
};
</script>

<style scoped>
.div__waveform {
  width: 100%;
  height: 244px;
  background: #000000;
  position: relative;
  top: 0px;
  left: 0px;
  z-index: 0;
  box-sizing: content-box;
  overflow: hidden;
  overflow-x: scroll;
}
::-webkit-scrollbar {
  -webkit-appearance: none;
  height: 15px;
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
.div__waveform-y-axis-title {
  display: flex;
  justify-content: center;
  line-height: 1;
  transform: rotate(270deg);
  padding: 5px;
  margin: 0px;
  overflow-wrap: break-word;
  color: #b7b7b7;
  font-family: Muli;
  font-weight: bold;
  position: absolute;
  top: 100px;
  left: -170px;
  width: 379px;
  overflow: hidden;
  user-select: none;
  font-size: 14px;
  letter-spacing: normal;
  z-index: 99;
  pointer-events: all;
  box-sizing: content-box;
}
.div__waveform-x-axis-title {
  display: grid;
  grid-template-columns: 20% 60% 20%;
  justify-items: start;
  line-height: 1;
  margin: 0px;
  color: #b7b7b7;
  font-family: Muli;
  font-weight: bold;
  position: sticky;
  top: 195px;
  left: 550px;
  width: 250px;
  height: 29px;
  user-select: none;
  font-size: 14px;
  letter-spacing: normal;
  z-index: 99;
  pointer-events: all;
  box-sizing: content-box;
  overflow: visible;
  text-align: start;
}
.div__waveform-graph {
  overflow: hidden;
  user-select: none;
  position: absolute;
  height: 200px;
  top: 15px;
  left: 14px;
  z-index: 1;
  font-family: Muli;
}
.g__waveform-x-axis {
  stroke: #b7b7b7;
  font-family: Muli;
  font-size: 11px;
}
.g__waveform-x-axis path {
  stroke: #4c4c4c;
}
.g__waveform-x-axis .tick line {
  stroke: #4c4c4c;
}
.g__waveform-y-axis {
  stroke: #b7b7b7;
  font-family: Muli;
  font-size: 11px;
}
.g__waveform-y-axis path {
  stroke: #4c4c4c;
}
.g__waveform-y-axis .tick line {
  stroke: #4c4c4c;
}
</style>
