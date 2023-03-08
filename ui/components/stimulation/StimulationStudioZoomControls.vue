<template>
  <div class="div__axis-controls">
    <span class="span__axis-controls-zoom-out-button" @click="zoomOut">
      <FontAwesomeIcon :icon="['fa', 'minus-circle']" />
    </span>

    <span class="span__axis-controls-zoom-in-button" @click="zoomIn">
      <FontAwesomeIcon :icon="['fa', 'plus-circle']" />
    </span>
  </div>
</template>
<script>
import { library } from "@fortawesome/fontawesome-svg-core";
import { faMinusCircle, faPlusCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add(faMinusCircle, faPlusCircle);

/**
 * @vue-props {String} axis - Determines which axis scale the controls change
 * @vue-data {String} zoomInMessage - Popover on hover for zoom in button
 * @vue-data {String} zoomOutMessage - Popover on hover for zoom out button
 * @vue-method {event} zoomIn - Commits the zoom-in to change corresponding scale
 * @vue-method {event} zoomOut - Commits the zoom-out to change corresponding scale
 */

export default {
  name: "StimulationStudioZoomControls",
  components: { FontAwesomeIcon },
  props: {
    axis: { type: String, default: "" },
  },
  data: function () {
    return {
      zoomInMessage: "Zoom-In",
      zoomOutMessage: "Zoom-Out",
    };
  },
  methods: {
    zoomIn() {
      if (this.axis === "y-axis") this.$store.commit("stimulation/setZoomIn", this.axis);
      else this.$emit("zoom-in");
    },
    zoomOut() {
      if (this.axis === "y-axis") this.$store.commit("stimulation/setZoomOut", this.axis);
      else this.$emit("zoom-out");
    },
  },
};
</script>
<style scoped>
.div__axis-controls {
  position: relative;
  left: 0px;
}

.span__axis-controls-zoom-out-button {
  text-align: center;
  font-weight: normal;
  position: relative;
  padding-right: 8px;
  height: 24px;
  width: 24px;
}
.span__axis-controls-zoom-in-button {
  font-weight: normal;
  position: relative;
  height: 24px;
  width: 24px;
}
* {
  -webkit-font-smoothing: antialiased;
}
span:hover {
  opacity: 0.8;
}
</style>
