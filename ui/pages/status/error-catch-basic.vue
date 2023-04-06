<template>
  <div>
    <ErrorCatchWidget logFilepath="C:\Users\Mantarray\AppData\Roaming\MantarrayController\stingray_logs" />
  </div>
</template>

<script>
// import { ErrorCatchWidget as ComponentToTest } from "@/dist/mantarray.common";
import ErrorCatchWidget from "@/components/status/ErrorCatchWidget.vue";

export default {
  components: {
    ErrorCatchWidget,
  },
};
</script>
