
if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside.clientside = {
    make_draggable: function (id, children) {
        setTimeout(function () {
            var drake = dragula({direction:"horizontal"});
            var el = document.getElementById(id)
            drake.containers.push(el);
            drake.on("drop", function (_el, target, source, sibling) {
                // a component has been dragged & dropped
                // get the order of the ids from the DOM
                var order_ids = Array.from(target.children).map(function (child) {
                    return child.id;
                });
                // in place sorting of the children to match the new order
                children.sort(function (child1, child2) {
                    return order_ids.indexOf(child1.props.id) - order_ids.indexOf(child2.props.id)
                });
                // How can I trigger an update on the children property
                // ???
            })
        }, 1)
        return window.dash_clientside.no_update
    }
}