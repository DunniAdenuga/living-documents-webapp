<template>

    <b-navbar toggleable="lg" type="dark" variant="dark" fixed="top">
      <b-navbar-brand :to="{ name: 'list', params: {} }">
        Living Documents
        <img src="https://assets.entrepreneur.com/content/3x2/2000/20191219170611-GettyImages-1152794789.jpeg"
             class="d-inline-block align-top" alt="Book" style="width:25px;height:25px;">
      </b-navbar-brand>
    </b-navbar>

</template>

<script>
export default {
  name: 'NavigationBar'
};
</script>

<style scoped>

</style>
