import React, {Component} from 'react';

import './BackgroundSelector.css';

class BackgroundSelector extends Component {
    static defaultProps = {
        value: "",
        placeHolder: "https://elly.dog",
        onSubmit: (val) => {}
    }

    constructor(props) {
        super(props);
        this.state = {
            value: props.value
        };

        this.onChange = this.onChange.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }

    onChange(e) {
        this.setState({value: e.target.value});
        e.preventDefault();
        e.stopPropagation();
    }

    onSubmit(e) {
        this.props.onSubmit(this.state.value);
        e.preventDefault();
        e.stopPropagation();
    }

    render() {
        return (
                <div className="upload-form">
                <input type="text" placeHolder={this.props.placeHolder} onChange={this.onChange}/>
                <a onClick={this.onSubmit}>Do the thing</a>
                </div>
        );
    }
}

export default BackgroundSelector;
