Component({properties:{section:{type:Object,value:{}}},methods:{add(){this.triggerEvent("add",{section:this.data.section});},editTime(){this.triggerEvent("edittime",{section:this.data.section});}}});
