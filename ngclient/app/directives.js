lampost.directive("enterKey", function() {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            element.bind('keypress', function(event) {
                if (event.keyCode == 13) {
                    scope.$eval(attrs.enterKey);
                    event.preventDefault();
                    return false;
                }
            })
        }
    }
});

lampost.directive('scrollBottom', ['$timeout', function($timeout) {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            scope.$watch(attrs.scrollBottom, function(newValue, oldValue) {
                $timeout(function () {
                    var scrollHeight = element[0].scrollHeight;
                    if (scrollHeight) {
                        element.scrollTop(scrollHeight);
                    }
                });
            })
        }
    };
}]);

lampost.directive('history', function() {
    return {
        restrict: 'A',
        link: function(scope, element, attr) {
            element.bind('keydown', function(event) {
                var apply = null;
                if (event.keyCode == 38) {
                    apply = function() {scope.historyUp()};
                } else if (event.keyCode == 40) {
                    apply = function() {scope.historyDown()};
                }
                if (apply) {
                    scope.$apply(apply);
                    event.preventDefault();
                    return false;
                }
            });
        }
    }
});

lampost.directive("prefFocus", ['$rootScope', '$timeout', function($rootScope, $timeout) {
    return {
        restrict: "A",
        link: function(scope, element) {
            scope.$on("refocus", forceFocus);
            var timer = $timeout(forceFocus);
            function forceFocus() {
                $timeout.cancel(timer);
                $(element)[0].focus();
            }
        }
    }
}]);