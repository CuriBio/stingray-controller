<template>
  <div class="protocol-viewer-background">
    <StimulationStudioWaveform
      :x_axis_sample_length="x_axis_sample_length"
      :y_min="-yAxisScale"
      :y_max="yAxisScale"
      :plot_area_pixel_height="160"
      :plot_area_pixel_width="dynamic_plot_width"
      :data_points="datapoints"
      :y_axis_label="stimulationType"
      :x_axis_label="x_axis_label"
      :repeatColors="repeatColors"
      :delayBlocks="delayBlocks"
    />
  </div>
</template>
<script>
import StimulationStudioWaveform from "@/components/stimulation/StimulationStudioWaveform.vue";
import { convertXYArraysToD3Array } from "@/js_utils/waveform_data_formatter.js";
import { mapState } from "vuex";

/**
 * @vue-props {Sting} stimulationType - Current selected stimulationType assigned to y axis label/scale
 * @vue-data {Int} y_min_max - The y axis min and max values
 * @vue-data {Array} datapoints - The d3 formatted x and y axis points
 * @vue-data {Array} repeatColors - Corresponding color assignments from repeat blocks in pulse order to be assigned to color of line in graph
 * @vue-data {Int} x_axis_sample_length - x-axis max value
 * @vue-data {Array} delayBlocks - Delay block to appear at end of graph to show in between repeats
 * @vue-data {String} x_axis_label - X axis label passed down to graph
 * @vue-method {Event} get_dynamic_sample_length - Calculates last point of line in graph for zoom feature

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
      x_axis_sample_length: 100,
      dynamic_plot_width: 1200,
      x_axis_label: "Time",
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
    last_x_value() {
      if (this.delayBlocks.length > 0) {
        return isNaN(this.delayBlocks[0][1])
          ? this.datapoints[this.datapoints.length - 1][0]
          : this.delayBlocks[0][1];
      } else return 0;
    },
  },
  watch: {
    datapoints: function () {
      if (this.last_x_value === 0) this.x_axis_sample_length = 100;
      else this.x_axis_sample_length = this.last_x_value + 50;

      if (this.x_axis_sample_length > 10000 && this.dynamic_plot_width === 1200)
        this.dynamic_plot_width *= 25;
    },
    protocolEditor: function () {
      this.x_axis_sample_length = 100;
      this.dynamic_plot_width = 1200;
    },
  },
  created: function () {
    this.unsubscribe = this.$store.subscribe(async (mutation) => {
      if (mutation.type === "stimulation/setZoomOut") {
        if (this.dynamic_plot_width === 1200) this.x_axis_sample_length *= 1.5;
        else if (this.dynamic_plot_width > 1200) this.dynamic_plot_width /= 1.5;
      }
      if (mutation.type === "stimulation/setZoomIn") {
        if (this.x_axis_sample_length > this.last_x_value + 50 || this.datapoints.length === 0)
          this.x_axis_sample_length /= 1.5;
        else this.dynamic_plot_width *= 1.5;
      }
    });
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
