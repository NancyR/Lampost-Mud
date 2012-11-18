angular.module('lampost', ['lampost_dir', 'lampost_svc']);

angular.module('lampost').config(['$routeProvider', '$locationProvider', function (
    $routeProvider, $locationProvider) {
    $routeProvider.
        when('/game', {templateUrl:'view/main.html'}).
        when('/settings', {templateUrl:'view/settings.html'}).
        otherwise({redirectTo:'/game'});
    $locationProvider.hashPrefix('!');
}]);


// Using here so they get instantiated.
//noinspection JSUnusedLocalSymbols
angular.module('lampost').run(['$rootScope', 'lmBus', 'lmRemote', 'lmData', 'lmDialog',
    function ($rootScope, lmBus, lmRemote, lmData, lmDialog) {
        window.onbeforeunload = function () {
            if (lmData.editorWindow && !lmData.editorWindow.closed) {
                return "Closing or reloading this window will close the editor.  Continue?";
            }
            return null;
        };

        window.onunload = function() {
            if (lmData.editorWindow && !lmData.editorWindow.closed) {
                lmData.editorWindow.close();
            }
            lmBus.dispatch("window_closing");
            window.windowClosing = true;
        };

        $rootScope.siteTitle = lampost_config.title;
        $('title').text(lampost_config.title);

        lmRemote.connect();
    }]);


angular.module('lampost').controller('NavController', ['$rootScope', '$scope', '$location', 'lmBus', 'lmData', 'lmUtil', 'lmDialog',
    function ($rootScope, $scope, $location, lmBus, lmData, lmUtil, lmDialog) {

        $(window).on("resize", function () {
            $rootScope.$apply(resize);
        });

        function resize() {
            var navbar = jQuery('#lm-navbar');
            var navBarMargin = parseInt(navbar.css('marginBottom').replace('px', ''));
            var gameHeight = $(window).height() - navbar.height() - navBarMargin;
            $rootScope.gameHeight = {height:gameHeight.toString() + 'px'};
            var editorHeight = gameHeight - lmUtil.getScrollBarSizes()[1];
            $rootScope.editorHeight = {height:editorHeight.toString() + 'px'};
        }

        resize();

        function Link(name, label, icon, priority) {
            this.name = name;
            this.label = label;
            this.icon = icon;
            this.priority = priority;
            this.active = function () {
                return $location.path() == '/' + this.name;
            };
            this.class = function () {
                return this.active() ? "active" : "";
            };
            this.iconClass = function () {
                return this.icon + " icon-white" + (this.active() ? "" : " icon-gray");
            };
        }

        var baseLinks = [new Link("game", "Mud", "icon-leaf", 0)];
        var settingsLink = new Link("settings", "Settings", "icon-user", 50);

        function validatePath() {
            $scope.welcome = 'Please Log In';
            $scope.loggedIn = false;
            $scope.links = baseLinks.slice();
            for (var i = 0; i < $scope.links.length; i++) {
                if ($scope.links[i].active()) {
                    return;
                }
            }
            $location.path(baseLinks[0].name);
        }

        $scope.changeLocation = function (name) {
            $location.path(name);
        };

        $scope.logout = function() {
            lmBus.dispatch("server_request", "action", {action:"quit"});
        };

        validatePath();
        lmBus.register("login", function () {
            $scope.links.push(settingsLink);
            $scope.welcome = 'Welcome ' + lmData.player.name;
            $scope.loggedIn = true;
        }, $scope);

        lmBus.register("logout", function(reason) {
            if (reason == "other_location") {
                var player = lmData.player ? lmData.player.name : "Unknown";
                lmDialog.showOk("Logged Out", player + " logged in from another location.");
            }
            validatePath();
        }, $scope, -500);
    }]);


angular.module('lampost').controller('GameController', ['$scope', 'lmBus', 'lmData', 'lmDialog',
    function ($scope, lmBus, lmData, lmDialog) {

        $scope.toolbar = [];
        update();

        lmBus.register("login", function() {
            update();

        }, $scope);

        lmBus.register("logout", function (reason) {
            if (reason == "invalid_session") {
                lmDialog.removeAll();
                lmDialog.showOk("Session Lost", "Your session has been disconnected.");
            }
            update();
        }, $scope);

        function launchEditor() {
            if (lmData.editorWindow && lmData.editorWindow.closed) {
                delete lmData.editorWindow;
            }
            if (lmData.editorWindow) {
                lmData.editorWindow.focus();
            } else {
                lmData.editorWindow = open("editor.html", "editor_" + lmData.playerId);
            }
        }

        function update() {
            $scope.toolbar = [];
            if (lmData.player) {
                $scope.actionPane = "action";
                if (lmData.player.editors) {
                    $scope.toolbar.push({label:'Editor', click:launchEditor});
                }
            } else {
                $scope.actionPane = "login";
            }

    }

    }]);


angular.module('lampost').controller('LoginController', ['$scope', 'lmRemote', 'lmDialog',
    function ($scope, lmRemote, lmDialog) {
    $scope.loginError = false;
    $scope.siteDescription = lampost_config.description;
    $scope.login = function () {
        lmRemote.request("login", {user_id:this.userId,
            password:this.password}).then(loginError);

    };

    $scope.newAccountDialog = function() {
        lmDialog.show({templateUrl:"dialogs/new_account.html", controller:"NewAccountController"});
    };

    function loginError(response) {
        if (response == "not_found") {
            $scope.loginError = true;
        }
    }
}]);

angular.module('lampost').controller('NewAccountController', ['$scope', 'lmRemote', function($scope, lmRemote) {

    $scope.accountName = "";
    $scope.playerName = "";
    $scope.password = "";
    $scope.passwordCopy = "";
    $scope.email = "";
    $scope.dirty = function() {
        $scope.errorText = null;
    };

    $scope.createAccount = function() {
        if ($scope.password != $scope.passwordCopy) {
            $scope.errorText = "Passwords don't match.";
            return;
        }
        if ($scope.accountName.indexOf(" ") > -1 ||
            $scope.playerName.indexOf(" ") > -1) {
            $scope.errorText = "Spaces not permitted in player or account names";
            return;
        }
        lmRemote.request("settings/create_account", {account_name:$scope.accountName,
            player_name:$scope.playerName,  password:$scope.password,  email:$scope.email}).then(function() {
                $scope.dismiss();
            }, function(error) {
                if (error.status == 409) {
                    $scope.errorText = error.data;
                }
            });
    }
}]);

angular.module('lampost').controller('ActionController', ['$scope', 'lmBus', 'lmData', function ($scope, lmBus, lmData) {
    var curAction;
    $scope.update = 0;
    $scope.action = "";
    $scope.display = lmData.display;
    lmBus.register("display_update", function () {
        $scope.display = lmData.display;
        $scope.update++;
    }, $scope);
    $scope.sendAction = function () {
        if ($scope.action) {
            lmBus.dispatch("server_request", "action", {action:$scope.action});
            lmData.history.push($scope.action);
            lmData.historyIx = lmData.history.length;
            $scope.action = "";
        }
    };
    $scope.historyUp = function () {
        if (lmData.historyIx > 0) {
            if (lmData.historyIx == lmData.history.length) {
                curAction = this.action;
            }
            lmData.historyIx--;
            this.action = lmData.history[lmData.historyIx];
        }
    };
    $scope.historyDown = function () {
        if (lmData.historyIx < lmData.history.length) {
            lmData.historyIx++;
            if (lmData.historyIx == lmData.history.length) {
                this.action = curAction;
            } else {
                this.action = lmData.history[lmData.historyIx];
            }
        }
    }
}]);
