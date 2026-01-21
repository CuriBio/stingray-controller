<template>
  <div>
    <div class="div__stimulation-modes-header">Stimulation Mode:</div>
    <div class="div__stimulation-modes-selection">
      <b-form-radio-group
        v-model="stimScheduleMode"
        :options="modes"
        name="radios-stacked"
        value-field="value"
        text-field="value"
        stacked
        @input="selectMode"
      ></b-form-radio-group>
    </div>
  </div>
</template>
<script>
import Vue from "vue";
import { BFormRadioGroup } from "bootstrap-vue";
Vue.component("BFormRadioGroup", BFormRadioGroup);
import { mapState, mapActions } from "vuex";

import { STIM_SCHEDULE_MODES } from "@/store/modules/stimulation/enums";

export default {
  name: "StimulationScheduleModes",
  computed: {
    ...mapState("stimulation", ["stimScheduleMode"]),
    modes() {
      return Object.keys(STIM_SCHEDULE_MODES);
    },
  },
  methods: {
    ...mapActions("stimulation", ["setStimScheduleMode"]),
    selectMode(mode) {
      this.setStimScheduleMode(mode);
    },
  },
};
</script>
<style type="text/css">
.div__stimulation-modes-header {
  font-style: italic;
  font-size: 17px;
  font-family: Muli;
  height: 26px;
  color: #fff;
}

.div__stimulation-modes-selection {
  white-space: nowrap;
  margin-bottom: 0;
  color: #fff;
  padding-left: 5px;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 15px;
}

.custom-radio .custom-control-label::before {
  background-color: #000;
}

.custom-radio .custom-control-input:checked ~ .custom-control-label::before,
.custom-radio .custom-control-input:checked ~ .custom-control-label::after {
  background-color: #000;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3E%3Ccircle r='1.5' fill='#FFF'/%3E%3C/svg%3E");
  border-radius: 50%;
  box-shadow: 0 0 0 1px #fff;
}

.custom-radio .custom-control-input:checked:hover ~ .custom-control-label::before,
.custom-radio .custom-control-input:checked:hover ~ .custom-control-label::after {
  background-color: #000;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='-4 -4 8 8'%3E%3Ccircle r='1.5' fill='#FFF'/%3E%3C/svg%3E");
  border-radius: 50%;
  box-shadow: 0 0 0 1px #fff;
}

.custom-radio .custom-control-input:active ~ .custom-control-label::before {
  color: #fff;
  background-color: #000;
}

.custom-radio .custom-control-input:focus ~ .custom-control-label::before,
.custom-radio .custom-control-input:focus ~ .custom-control-label::after {
  color: #fff;
  border-radius: 50%;
  box-shadow: 0 0 0 1px #fff;
}

.custom-radio .custom-control-input:hover ~ .custom-control-label::before,
.custom-radio .custom-control-input:hover ~ .custom-control-label::after {
  border-radius: 50%;
  box-shadow: 0 0 0 1px #fff;
}

.custom-control-label:after {
  background: none;
}
</style>
