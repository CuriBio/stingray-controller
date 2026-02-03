<template>
  <div>
    <span class="span__stim-controls-settings-button">
      <FontAwesomeIcon :icon="['fa', 'cog']" />
    </span>
  </div>
</template>
<script>
import { library } from "@fortawesome/fontawesome-svg-core";
import { faCog } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add(faCog);

export default {
  name: "PlayerControlsSettingsButton",
  components: { FontAwesomeIcon },
};
</script>
<style type="text=css">
.span__stim-controls-settings-button {
  text-align: center;
  position: absolute;
  width: 30px;
  height: 30px;
  line-height: 30px;
  top: 0px;
  left: 0px;
  color: #2f2f2f;
  font-size: 41px;
}

#settings-form {
  position: fixed;
  margin: 5% auto;
  top: 10%;
  left: 0;
  right: 0;
}
</style>
