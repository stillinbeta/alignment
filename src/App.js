import React, { Component } from 'react';
import './App.css';
import {me, guilds} from './Data.js';


class DiscordImage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            dim: false,
            hover: false
        };
    }

    handleClick(e) {
        this.setState((prevstate, props) => ({
            dim: !prevstate.dim
        }));
    }

    handleHover(e) {
        this.setState({hover: true});
    }

    handleBlur(e) {
        this.setState({hover: false});
    }

    render() {
        return (
                <img src={
                    this.props.baseURL +
                        this.props.objectID +
                        "/" +
                        this.props.imageID +
                        ".png"}
            class={(this.state.dim ? "dim" : "") + " " + (this.state.hover ? "squareround" : "")}
            onClick={this.handleClick.bind(this)}
            onMouseOver={this.handleHover.bind(this)}
            onMouseOut={this.handleBlur.bind(this)}
            alt={this.props.altText}
                />
        );
    }
}

class GuildList extends Component {
    render() {
        const guilds = this.props.guilds;
        const guildIcons = guilds.map(
            (guild) => <li key={guild.id}><GuildIcon guild={guild} /></li>
        );
        return (
                <ul class="guildIcons">{guildIcons}</ul>
        );
    }
}

class GuildIcon extends Component {
    render() {
        return (
            <DiscordImage
            baseURL="https://cdn.discordapp.com/icons/"
            objectID={this.props.guild.id}
            imageID={this.props.guild.icon}
            altText={this.props.guild.name}
                />
        );
    }
}

class UserAvatar extends Component {
    render() {
        return (
                <DiscordImage
            baseURL="https://cdn.discordapp.com/avatars/"
            objectID={this.props.user.id}
            imageID={this.props.user.avatar}
            altText={this.props.user.username}
                />
        );
    }


}

class App extends Component {
  render() {
    return (
      <div className="App">
        <UserAvatar user={me} />
            <hr />
        <GuildList guilds={guilds} />
      </div>
    );
  }
}

export default App;
