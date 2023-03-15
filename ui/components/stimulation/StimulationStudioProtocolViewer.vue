<template>
  <div class="protocol-viewer-background">
    <StimulationStudioWaveform
      :xAxisSampleLength="xAxisSampleLength"
      :yMin="-yAxisScale"
      :yMax="yAxisScale"
      :plotAreaPixelHeight="160"
      :plotAreaPixelWidth="dynamicPlotWidth"
      :dataPoints="datapoints"
      :yAxisLabel="stimulationType"
      :xAxisLabel="xAxisLabel"
      :repeatColors="repeatColors"
      :delayBlocks="delayBlocks"
      @zoom-out="zoomOutXAxis"
      @zoom-in="zoomInXAxis"
    />
  </div>
</template>
<script>
import StimulationStudioWaveform from "@/components/stimulation/StimulationStudioWaveform.vue";
import { convertXYArraysToD3Array } from "@/js-utils/WaveformDataFormatter.js";

import { mapState } from "vuex";

/**
 * @vue-props {Sting} stimulationType - Current selected stimulationType assigned to y axis label/scale
 * @vue-data {Int} yMinMax - The y axis min and max values
 * @vue-data {Array} datapoints - The d3 formatted x and y axis points
 * @vue-data {Array} repeatColors - Corresponding color assignments from repeat blocks in pulse order to be assigned to color of line in graph
 * @vue-data {Int} xAxisSampleLength - x-axis max value
 * @vue-data {Array} delayBlocks - Delay block to appear at end of graph to show in between repeats
 * @vue-data {String} xAxisLabel - X axis label passed down to graph
 * @vue-method {Event} getDynamicSampleLength - Calculates last point of line in graph for zoom feature

 */

export default {
  name: "StimulationStudioProtocolViewer",
  components: {
    StimulationStudioWaveform,
  },
  props: {
    stimulationType: { type: String, default: "Voltage" },
  },
  data() {
    return {
      xAxisSampleLength: 100,
      dynamicPlotWidth: 1200,
      xAxisLabel: "Time",
    };
  },
  computed: {
    ...mapState("stimulation", [
      "xAxisValues",
      "yAxisValues",
      "yAxisScale",
      "delayBlocks",
      "repeatColors",
      "protocolEditor",
    ]),
    datapoints() {
      return convertXYArraysToD3Array(this.xAxisValues, this.yAxisValues);
    },
    lastXValue() {
      if (this.delayBlocks.length > 0) {
        return isNaN(this.delayBlocks[0][1])
          ? this.datapoints[this.datapoints.length - 1][0]
          : this.delayBlocks[0][1];
      } else return 0;
    },
  },
  watch: {
    datapoints: function () {
      if (this.lastXValue === 0) this.xAxisSampleLength = 100;
      else this.xAxisSampleLength = this.lastXValue + 50;

      if (this.xAxisSampleLength > 10000 && this.dynamicPlotWidth === 1200) this.dynamicPlotWidth *= 25;
    },
    protocolEditor: function () {
      this.xAxisSampleLength = 100;
      this.dynamicPlotWidth = 1200;
    },
  },

  methods: {
    zoomOutXAxis: function () {
      if (this.dynamicPlotWidth === 1200) this.xAxisSampleLength *= 1.5;
      else if (this.dynamicPlotWidth > 1200) this.dynamicPlotWidth /= 1.5;
    },
    zoomInXAxis: function () {
      if (this.xAxisSampleLength > this.lastXValue + 50 || this.datapoints.length === 0)
        this.xAxisSampleLength /= 1.5;
      else this.dynamicPlotWidth *= 1.5;
    },
  },
};
</script>
<style scoped>
.protocol-viewer-background {
  background: rgb(0, 0, 0);
  position: absolute;
  height: 50%;
  width: 1315px;
  height: 220px;
  overflow: visible;
}
</style>
