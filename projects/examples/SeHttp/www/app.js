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
                   </li>
                    
        `,

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
                    {item: "System", screen: "uPyScreenSystem"}
                ],
                menu_collapse: true

            }
        },
        template: `

                <nav class="navbar navbar-toggleable-md navbar-light bg-faded navbar-fixed-top">
                <!--class="navbar navbar-toggleable-md navbar-light bg-faded navbar-fixed-top-->
                      <button v-on:click.stop.prevent="setActive" class="navbar-toggler navbar-toggler-right" type="button" data-toggle="collapse" data-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
                        <span class="navbar-toggler-icon"></span>
                      </button>
                      <a class="navbar-brand" href="#">uPY</a>
                    <div :class="{'collapse ': menu_collapse }" class="navbar-collapse" id="navbarSupportedContent">
                      <div >
                        <ul class="navbar-nav mr-auto">
                                <uPyMenuButton v-for="menu in menus" :item="menu.item" :screen="menu.screen" :key="menu.item" ></uPyMenuButton>
                        </ul>
                      </div>
                </nav>
        `,

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
    //
    //SCREENS

    // //Body SCREEN HOME
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
       
                    <span v-if=!isOn class="badge badge-success">ON</span>
                    <span v-else class="badge badge-warning">OFF</span>
                    
                    </div>
                    
        `,

        methods: {
            changeState(ev){
                this.isOn = !this.isOn
                this.getfromupy('/led?set=&state=')
            },
            //
            // checkboxToggle (){
            //     // this.isChecked = !this.isChecked;
            // },
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
                    </div>
        `,
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
                        
                        
                        <!--<div class="progress">-->
                              <!--<div class="progress-bar bg-success" style="width:40%">-->
                                <!--Free Space-->
                              <!--</div>-->
                              <!--<div class="progress-bar bg-warning" style="width:10%">-->
                                <!--Warning-->
                              <!--</div>-->
                              <!--<div class="progress-bar bg-danger" style="width:20%">-->
                                <!--Danger-->
                              <!--</div>-->
                        <!--</div>-->
                        
                  </div>
        `,

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
            set_mem(){


            }

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
                </div>
        `,
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

// new Vue({
//   el: '#app',
//   data: {
//     msg: 'Show the message.'
//   },
//   methods: {
//     hello () {
//       alert('This is the message.')
//     }
//   },
//   render(h) {
//     return (
//       <span class={{ 'my-class': true }} on-click={ this.hello } >
//         { this.msg }
//       </span>
//     )
//   }
// });

//   new Vue({
//   el: '#app',
//   data: {
//     msg: 'Click to see the message'
//   },
//   methods: {
//     hello () {
//       alert('This is the message')
//     }
//   },
//   render (createElement) {
//     return createElement(
//       'span',
//       {
//         class: { 'my-class': true },
//         style: { cursor: 'pointer' },
//         on: {
//           click: this.hello
//         }
//       },
//       [ this.msg ]
//     );
//   },
// });



//     Vue.component('component-a', {
//   ...
//   methods: {
//     emitMethod () {
//        EventBus.$emit('EVENT_NAME', payLoad);
//     }
//   }
// });
//
//     Vue.component(‘component-b’, {
//   ...
//   mounted () {
//     EventBus.$on(‘EVENT_NAME’, function (payLoad) {
//       ...
//     });
//   }
// });
//
//     new Vue({
//   el: "#app",
//   components: {
//     ComponentA,
//     ComponentB
//   }
// });



    // Vue.use(Vuex);
    //
    // const store = new Vuex.Store({
    //       state: {
    //         count: 0
    //       },
    //       mutations: {
    //         increment (state) {
    //           state.count++
    //         }
    //       }
    // })
    //
    // const Counter = {
    //   template: `<div>{{ count }}</div>`,
    //   computed: {
    //     count () {
    //       return this.$store.state.count
    //     }
    //   }
    // }
    //
    // const app = new Vue({
    //   el: '#app',
    //   // указываем хранилище в опции "store", что обеспечит
    //   // доступ к нему также и для всех дочерних компонентов
    //   store,
    //   components: { Counter },
    //   template: `
    //     <div class="app">
    //       <counter></counter>
    //     </div>
    //   `
    // })


    // // <doggie v-model="speaks" :value="name"/>
    //
    //
    // Vue.component('doggie', {
    //   template: `
    //     <div>
    //       <h1>{{value}}'s says: {{sound}}</h1>
    //       <input :value="sound" @input="$emit('updateSound', $event.target.value)"  />
    //     </div>
    //   `,
    //   props: ['sound', 'value'],
    //   model: {
    //     prop: 'sound',
    //     event: 'updateSound'
    //   },
    // })
    //
    // new Vue({
    //   el: '#app',
    //   data: {
    //     speaks: 'bark!',
    //     name: 'Fluffy'
    //   },
    //   mounted() {
    //     const vm = this
    //     setInterval(() => { console.log('dog sound', this.speaks); }, 3000);
    //   }
    // })











//exam0 - my
    // //MENU
    // Vue.component ('upy-menu',{
    //
    //     data: function(){
    //         return {
    //             menus:[
    //                 {item: "Home", screen: "upy-home"},
    //                 {item: "Switch", screen: "upy-switch"}
    //             ],
    //         }
    //
    //     },
    //     template: `
    //                 <ul class="nav navbar-nav"  id="wMenu">
    //                     <li v-for="menu in menus" >
    //                         <a v-on:click.stop.prevent="changeScreen(menu.screen)" href="#">{{ menu.item}}</a>
    //                     </li>
    //                 </ul>
    //     `,
    //     methods: {
    //         changeScreen(screen){
    //             this.$emit('increment', screen);
    //             this.$parent.current = screen;
    //             console.log(screen);
    //         }
    //     },
    //
    // });
    //
    //
    //
    // //SCREEN HOME
    // Vue.component ('upy-home',{
    //
    //     template: `<div>
    //                 <h1>Home</h1>
    //                 <p>whatever contents here</p>
    //               </div>
    //     `,
    // });
    //
    // //SCREEN SWITCH
    // Vue.component ('upy-switch',{
    //
    //     template: `<div>
    //                 <h1>Switch</h1>
    //                 <p>whatever contents here</p>
    //               </div>
    //     `,
    // });
    //
    //
    // //SCREEN-MAIN
    // Vue.component ('upy-screen',{
    //
    //     props:   {
    //         initialScreen: {default: 'upy-home'}
    //
    //     },
    //
    //     data: function () {
    //         return { current: this.initialScreen }
    //     },
    //
    //
    //     template: `
    //                 <component :is="current"></component>
    //     `,
    //
    //      components:['upy-switch','upy-home'],
    // });

 //-----------exam1
    // // create component proxy
    //
    // Vue.component('component-proxy', {
    //   props: {
    //     name: {
    //       type: String,
    //       required: true
    //     },
    //     props: {
    //       type: Object,
    //       default: () => {}
    //     }
    //   },
    //
    //   render(createElem) {
    //     return createElem(this.name, {
    //       attrs: this.props
    //     });
    //   }
    // });
    //
    // // create example simple text component
    //
    // Vue.component('simple-text', {
    //   props: ['content'],
    //   template: `
    //     <p>
    //       <strong>Simple Text says</strong>:
    //       <span v-text="content"></span>
    //     </p>
    //   `
    // });
    //
    //
    //
    // //APP
    // Vue.component ('app',{
    //       data() {
    //         return {
    //           name: 'simple-text',
    //           props: {
    //             content: "I've been proxied!"
    //           }
    //         }
    //       },
    //       template: `
    //         <div>
    //           <simple-text content="Here I am for real" />
    //           <component-proxy :name="name" :props="props" />
    //         </div>
    //       `
    // });
    //
    //
    // //render APP
    // new Vue({
    //
    //     el: '#myapp',
    //     render: c => c(Vue.component('app'))
    // });


});




