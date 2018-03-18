import React, {Component} from 'react';

import './NavMenu.css';
import BackgroundSelector from './BackgroundSelector.js';

class NavMenu extends Component {
    constructor(props) {
        super(props);
        this.state = {
            upload: false
        };

        this.newImage = this.newImage.bind(this);
        this.handleImage = this.handleImage.bind(this);

    }

    newImage() {
        this.setState({upload: true});
        console.log("new image time");
    }

    handleImage(imageURL) {
        this.setState({upload: false});
        console.log(imageURL);
    }

    render() {
        return (
                <nav>
                <a onClick={this.newImage}>New Image</a>
                { this.state.upload &&
                  <BackgroundSelector onSubmit={this.handleImage} />
                }
                <a href="/logout">Logout</a>
                </nav>
        );
    }
}

export default NavMenu;
