<template>
  <div>
    <div class="div__stimulation-modes-header">Stimulation Mode:</div>
    <div class="div__stimulation-modes-selection">
      <b-form-radio-group
        v-model="stimScheduleMode"
        :options="options"
        :disabled="radioGroupInfo.disabled"
        name="radios-stacked"
        value-field="value"
        text-field="value"
        stacked
        @input="selectMode"
      ></b-form-radio-group>
    </div>
    <div
      v-if="radioGroupInfo.disabled"
      v-b-popover.hover.bottom="radioGroupInfo.tooltip"
      class="div__stimulation-modes-blocker"
    />
  </div>
</template>
<script>
import Vue from "vue";
import { BFormRadioGroup } from "bootstrap-vue";
Vue.component("BFormRadioGroup", BFormRadioGroup);
import { mapState, mapActions } from "vuex";

import { SYSTEM_STATUS } from "@/store/modules/system/enums";
import { STIM_STATUS, STIM_SCHEDULE_MODES } from "@/store/modules/stimulation/enums";

export default {
  name: "StimulationScheduleModes",
  computed: {
    ...mapState("stimulation", ["stimScheduleMode", "stimStatus"]),
    ...mapState("system", ["statusUuid", "systemErrorCode"]),
    options() {
      return Object.keys(STIM_SCHEDULE_MODES);
    },
    radioGroupInfo() {
      if (this.systemErrorCode) {
        return { disabled: true, tooltip: "Cannot change stimulation mode while there is an error." };
      } else if ([SYSTEM_STATUS.GOING_OFFLINE_STATE, SYSTEM_STATUS.OFFLINE_STATE].includes(this.statusUuid)) {
        return { disabled: true, tooltip: "Cannot change stimulation mode while in offline mode." };
      } else if (this.statusUuid === SYSTEM_STATUS.IDLE_READY_STATE) {
        // depends entirely on stim status in this case
        if ([STIM_STATUS.SHORT_CIRCUIT_ERROR, STIM_STATUS.ERROR].includes(this.stimStatus)) {
          return { disabled: true, tooltip: "Cannot change stimulation mode while there is an error." };
        } else if ([STIM_STATUS.STIM_ACTIVE, STIM_STATUS.WAITING].includes(this.stimStatus)) {
          return { disabled: true, tooltip: "Cannot change stimulation mode while stimulating." };
        } else if (this.stimStatus === STIM_STATUS.CONFIG_CHECK_IN_PROGRESS) {
          return {
            disabled: true,
            tooltip: "Cannot change stimulation mode while running configuration check.",
          };
        } else {
          return { disabled: false };
        }
      } else {
        // catch all message for every other state
        return { disabled: true, tooltip: "Cannot change stimulation mode at the moment." };
      }
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

.div__stimulation-modes-blocker {
  position: absolute;
  left: -10px;
  top: 23px;
  width: 200px;
  height: 53px;
  z-index: 5;
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

.custom-control-input:disabled ~ .custom-control-label:before,
.custom-control-input[disabled] ~ .custom-control-label:before {
  background-color: #444;
}

.custom-radio .custom-control-input:disabled:checked ~ .custom-control-label:after {
  background-color: #444;
}

.custom-control-label:after {
  background: none;
}
</style>
