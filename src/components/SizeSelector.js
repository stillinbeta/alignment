import React, { Component } from 'react';

import './Slider.css';
import './SizeSelector.css';
import UserAvatar from './UserAvatar.js';

class SizeSelector extends Component {
    static defaultProps = {
        onSizeChange: (v) => {}
    }
    constructor(props) {
        super(props);
        this.state = {
            value: props.value
        };
        this.onChange = this.onChange.bind(this);
    }

    onChange(e) {
        var value = e.target.value;
        this.setState({value: value});
        e.stopPropagation();
        e.preventDefault();

        this.props.onSizeChange(value);
    }

    render() {
        return (
            <div className="size-selector-container">

                <div className="size-example-small">
                    <UserAvatar className="" size={this.props.min} user={this.props.user} />
                </div>
                <div className="slider-box">
                        <input type="range"
                    value={this.state.value}
                    min={this.props.min}
                    max={this.props.max}
                    onChange={this.onChange}
                    className="size-selector"
                        />
                </div>

                <div className="size-example-large">
                    <UserAvatar className="size-example-large" size={this.props.max} user={this.props.user} />
                </div>
            </div>
        );
    }
}

export default SizeSelector;
