define(["vue", "axios", "underscore", 'css!style' ], function (Vue, axios, _) {
    'use strict';

    Vue.config.devtools = true;
    Vue.config.debug = true;

    var bus = new Vue()

    //MENU
    Vue.component ('uPyMenuButton',{
        data: function(){
                return {
                    activeItem: '',
                }
        },
        props: ['item', 'screen'],
        template: `
                    <li class="nav-item" :class="{'active': isActive(item)}" >
                            <a class="nav-link" v-on:click.stop.prevent="changeScreen"  href="#">{{item}}</a>
                   </li>`,
        methods: {
            changeScreen(){
                bus.$emit('screen-selected', this.screen);
                bus.$emit('menu-button-selected', this.item);
            },
            isActive: function (menuItem) {
                return this.activeItem === menuItem
            },
        },
        created () {
            bus.$on('menu-button-selected', (item) => {
                this.activeItem = item
            })
        },
    });



    Vue.component ('uPyMenu',{
        data: function(){
            return {
                menus:[
                    {item: "Home", screen: "uPyScreenHome"},
                    {item: "Switch", screen: "uPyScreenSwitch"},
                    {item: "System", screen: "uPyScreenSystem"},
                    {item: "WiFi", screen: "uPyScreenWifi"}
                ],
                menu_collapse: true
            }
        },
        template: `
                <nav class="navbar navbar-toggleable-md navbar-light bg-faded navbar-fixed-top">
                <!--class="navbar navbar-toggleable-md navbar-light bg-faded navbar-fixed-top-->
                      <button v-on:click.stop.prevent="setActive" class="navbar-toggler navbar-toggler-right" 
                      type="button" data-toggle="collapse" data-target="#navbarSupportedContent" 
                      aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                        <span class="navbar-toggler-icon"></span>
                      </button>
                      <a class="navbar-brand" href="#">uPY</a>
                    <div :class="{'collapse ': menu_collapse }" class="navbar-collapse" id="navbarSupportedContent">
                      <div >
                        <ul class="navbar-nav mr-auto">
                                <uPyMenuButton 
                                v-for="menu in menus" 
                                :item="menu.item" 
                                :screen="menu.screen" 
                                :key="menu.item" ></uPyMenuButton>
                        </ul>
                      </div>
                </nav>`,
        methods: {
            isActive: function () {
                return this.menu_collapse
            },
            setActive: function () {
                this.menu_collapse = !this.menu_collapse
            },
        },
        created () {
            bus.$on('menu-button-selected', () => {
                this.menu_collapse = true
            })
        },
    });


    //SCREENS
    //Body SCREEN HOME
    Vue.component ('uPyScreenWifi',{
        template: `<div>
                    <h1>WiFi</h1>
                    <p>whatever contents here</p>
                  </div>
        `,
    });



    //Body SCREEN HOME
    Vue.component ('uPyScreenHome',{
        template: `<div>
                    <h1>Home</h1>
                    <p>whatever contents here</p>
                  </div>
        `,
    });

    //SCREEN SWITCH
    Vue.component ('uPySwitchButton',{
        data: function(){
                return {
                    isOn: 1,
                    posts: [],
                    errors: [],
                    interval: null,
                }
        },
        props: ['item'],
        template: `
                    <div>
                    <label class="btn btn-secondary" v-on:click="changeState">
                    ON/OFF
                            <!--<input disabled="disabled" type="checkbox" :checked=isOn > On-->
                            <!--<input disabled="disabled" type="checkbox" :checked=!isOn > Off-->
                    </label>
       
                    <span v-if=isOn class="badge badge-success">ON</span>
                    <span v-else class="badge badge-warning">OFF</span>
                    
                    </div>`,
        methods: {
            changeState(ev){
                this.isOn = !this.isOn
                this.getfromupy('/led?set=&state=')
            },
            getfromupy(api){

                const vm = this;
                axios.get(api)
                      .then(function (response) {
                            vm.posts = response.data
                          if (vm.posts){
                               vm.isOn = parseInt(vm.posts["state"])
                           }
                            // console.log(vm.posts);
                      })
                      .catch(function (e) {
                            vm.posts = []
                            vm.errors.push(e)
                            vm.isOn = 1

                            // console.log(e);
                      });
            }
        },
        created(){
            this.getfromupy('/led?state=')
            this.interval = setInterval(function () {
                  this.getfromupy('/led?state=');
                }.bind(this), 15000);
        },
         beforeDestroy: function(){
                clearInterval(this.interval);
        }
    });


    Vue.component ('uPyScreenSwitch',{

        data: function () {
            return { item: 'LED On/Off' }
        },

        template: `<div>
                        <h1>Switch</h1>
                       <uPySwitchButton :item="item"></uPySwitchButton>
                    </div>`,
    });

    //Body SCREEN System
    Vue.component ('uPyScreenSystem',{
        data: function(){
                return {
                    posts: [],
                    errors: [],
                    interval: null,

                }
        },
        template: `<div>
                    <h1>System</h1>
                        <p>Allocated: "{{ c_m_alloc }}"</p>
                        <p>Free: "{{ c_m_free }}"</p>
                        <p>Capacity: "{{ c_m_capacity }}"</p>
                        <p>Usage: 
                          <div class="progress">
                    
                                <div class="progress-bar" v-bind:style="{ 'width': c_m_usage }">{{ c_m_usage }}</div>
                          </div>
                        </p>
                    </div>`,

        computed: {
            c_m_alloc: function () {
                  if (this.posts.memory && this.posts.memory.mem_alloc){
                     return parseInt(this.posts.memory.mem_alloc)
                  }
                  return 0
            },
            c_m_free: function () {
                  if (this.posts.memory && this.posts.memory.mem_free){
                     return parseInt(this.posts.memory.mem_free)
                  }
                  return 0
            },
            c_m_capacity: function () {
              return this.c_m_alloc + this.c_m_free
            },
            c_m_usage: function () {
                //return "75%"
                return Math.round((this.c_m_capacity - this.c_m_free) / this.c_m_capacity * 100.0)+"%";
             }
        },
        methods: {
            getfromupy(api){
                const vm = this;
                axios.get(api)
                      .then(function (response) {
                            vm.posts = response.data
                            // console.log(vm.posts);
                      })
                      .catch(function (e) {
                            vm.posts = []
                            vm.errors.push(e)
                            vm.isOn = 1
                            // console.log(e);
                      });
            },
        },
        created(){
            this.getfromupy('/system?memory=')
            this.interval = setInterval(function () {
                  this.getfromupy('/system?memory=');
                }.bind(this), 5000);
        },
         beforeDestroy: function(){
                clearInterval(this.interval);
        }
    });


    //SCREEN-uPy
    Vue.component ('uPyScreen',{
        data: function () {
            return { current: 'uPyScreenHome' }
        },
        template: `
                <div class="container body-content" >
                    <component :is="current" ></component>
                </div>`,
        created () {
            bus.$on('screen-selected', (screen) => {
                this.current = screen
                // console.log('Screen has been triggered', screen)
        })
        },
    });



    //SCREEN HOME
    Vue.component ('uPyApp',{

        template: `
                    <div>
                        <uPyMenu></uPyMenu>
                        <uPyScreen></uPyScreen>
                    </div>
                    </div>
        `,
    });

        // //render APP
    new Vue({

        el: '#app',
        render: c => c(Vue.component('uPyApp'))
    });


});




