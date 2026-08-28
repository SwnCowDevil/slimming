Component({
  properties:{recipe:Object,showSave:{type:Boolean,value:false}},
  methods:{
    open(){this.triggerEvent("open",{recipe:this.data.recipe});},
    save(){this.triggerEvent("save",{recipe:this.data.recipe});}
  }
});
