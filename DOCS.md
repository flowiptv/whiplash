# documentation!

## Functions

### `mainloop()`
Actually runs the app.

### `sidebar_open()`
Opens the sidebar and sets focus to the first element.

### `load_config(<path>) -> dict`
Load a config from a path.

### `save_config(<config:dict>, <path>) -> none`
Save a config to a path.

### `set_layout(<id>)`
Sets the current layout to an id.

### `get_element_pointer(<path>) -> dict`
Returns the element for a path.
A path is a list of ids, with the layout element being first. Delimeted by `:`.
Example: `main:list:button`

## Layout and elements
An element is raw json.
It has two important keys - `type`, `width`, `height`, and `id`
`type` is for doing different element types.
`id` is for differentiating elements between eachother in one container.
`width` and `height` (or, `x` and `y` in `scatter` elements) are in "units"
units are a part of a virtual 16:9, 48x27 grid.
`focus` - Make the element focusable and enables action.
`action` - Set a function when the element has been clicked. Passes the element to the function.
`margin` - margin.
`padding` - padding.
## Element types

### list
`direction` [`horizontal` / `vertical`] - Orientation the elements are going to go in.
`scroll` [`False` / `True`] - Makes the list scrollable.
 - `anim_speed` [Float, `0` to `1`] - Speed of the animation. Uses `lerp` underneath.
`stretch` - Make all elements try to get as much space as possible.

### scatter
(none)

Elements require `x` and `y` to be properly positioned.

### progress
`value` - The value of the progress bar
`max` - Maximum value of the progress bar.

### image
`fit_mode` [`stretch` / `contain`] - The mode used to fit the image.
`image_surf` - Pygame surface to draw
OR
`path` - Path to an image

### label
`label` - Text to render. One line is 1 unit.
`small` - Use the small text. Makes one line 0.5 units.

### checkbox
`label` - Text to render. One line is 1 unit.
`checked` - Is the checkbox checked?
`action` triggers on checkbox change.

### textinput
`label` - Label on top of the input box.
`value` - Current text in the input box
`placeholder` - Placeholder for the input box.
`action` triggers on pressing enter.

### button
`label` - Label.
`action` triggers on button press.
`image` (Optional) - Path to an image.

## Layouts
Layouts live in the variable `layouts` (dict) inside the library.
You can edit the layouts by setting them.
Each layout is `<id>: <container>`
so they are surprisingly flexible
One thing that should be noted, the layout's container should be 48x27.

### `set_layouts(<layouts>)`
Sets the layouts to a new dict of layouts.

### `set_sidebar_items(<items>)`
Set sidebar items. 
The sidebar acts as a list which you can open by moving the focus out of bounds to the left.