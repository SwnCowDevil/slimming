Component({properties:{recipe:Object},methods:{open(){this.triggerEvent("open",{recipe:this.data.recipe});}}});
