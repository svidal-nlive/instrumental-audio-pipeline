# DNS Configuration for Instrumental Maker

To access your Instrumental Maker dashboard via the configured subdomains, you need to set up DNS records pointing to your server.

## Required DNS Records

Add the following A records to your `vectorhost.net` domain:

```
instrumental.vectorhost.net      A    [YOUR_SERVER_IP]
instrumental-api.vectorhost.net  A    [YOUR_SERVER_IP]
```

## Alternative: Local Testing

If you want to test locally before setting up DNS, add these entries to your `/etc/hosts` file:

```
[YOUR_SERVER_IP]  instrumental.vectorhost.net
[YOUR_SERVER_IP]  instrumental-api.vectorhost.net
```

## Deployment Steps

1. **Ensure Traefik is running:**
   ```bash
   cd ~/homelab/stacks/traefik
   docker-compose up -d
   ```

2. **Deploy Instrumental Maker:**
   ```bash
   cd ~/homelab/projects/instrumental-maker-2.0
   ./deploy-traefik.sh
   ```

3. **Access the application:**
   - Frontend: https://instrumental.vectorhost.net
   - API: https://instrumental-api.vectorhost.net
   - API Docs: https://instrumental-api.vectorhost.net/docs

## Security (Optional)

To enable authentication, uncomment the middleware lines in `docker-compose.traefik.yml`:

```yaml
# - "traefik.http.routers.instrumental.middlewares=forward-auth"
# - "traefik.http.routers.instrumental-api.middlewares=forward-auth"
```

This will require users to authenticate via your OAuth setup before accessing the application.

## Troubleshooting

- Check Traefik dashboard: http://[YOUR_SERVER_IP]:8080
- View logs: `docker-compose -f docker-compose.traefik.yml logs -f`
- Verify certificates: Check Let's Encrypt logs in Traefik
