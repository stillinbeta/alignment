import React, {Component} from 'react';

import DiscordImage from './DiscordImage.js';

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

export default UserAvatar;
