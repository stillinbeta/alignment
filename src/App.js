import React, { Component } from 'react';
import './App.css';
import {me, members} from './Data.js';
import Draggable from 'react-draggable';

class AvatarField extends Component {
    constructor(props) {
        super(props);
        this.state = {
            icons: props.icons,
            avatarSize: props.avatarSize

        };

        this.onSizeChange = this.onSizeChange.bind(this);
    }

    onSizeChange(newSize) {
        this.setState({avatarSize: newSize});
    }

    render() {
        const avatars = this.state.icons.map(
            (avatar) =>
                <Draggable
            defaultPosition={avatar.position}
            bounds="parent"
            key={avatar.user.id}
                >
                <UserAvatar user={avatar.user} size={this.state.avatarSize}/>
                </Draggable>
        );
        return (
            <div>
                <SizeSelector value={this.state.avatarSize} min="32" max="128"
            onSizeChange={this.onSizeChange}/>
                <div id="avatar-field">
                {avatars}
                </div>
           </div>
        );
    }
}

class SizeSelector extends Component {
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

        if (typeof this.props.onSizeChange !== "undefined") {
            this.props.onSizeChange(value);
        }
    }

    render() {
        return (
                <input type="range"
            value={this.state.value}
            min={this.props.min}
            max={this.props.max}
            onChange={this.onChange}/>
        );
    }
}

class AvatarMenu extends Component {
    render() {
        return (
            <div id="avatar-menu">
                <UserAvatar user={this.props.user} />
            </div>
        );
    }
}

class UserAvatar extends Component {
    render() {
        const {user, ...others} = this.props;
        return (
                <DiscordImage
            {...others}
            baseURL="https://cdn.discordapp.com/avatars/"
            objectID={user.id}
            imageID={user.avatar}
            altText={user.username}
                />
        );
    }
}

class DiscordImage extends Component {
    render() {
        var {
            objectID,
            imageID,
            baseURL,
            altText,
            className,
            size,
            ...others
        } = this.props;
        const imageSize = Math.pow(2, Math.round(Math.log2(size)));
        const url = `${baseURL}${objectID}/${imageID}.png?size=${imageSize}`;
        return (
                <img {...others}
            src={url} height={size} width={size}
            className={className + " icon "}
            alt={this.props.altText}
                />
        );
    }
}

class App extends Component {
  render() {
    return (
      <div className="App">
        <AvatarMenu user={me} />
        <AvatarField icons={members} avatarSize="64"/>
      </div>
    );
  }
}

export default App;
