# Testing GoCardless Payments

First off, you'll need a GoCardless sandbox account. 
[Sign up for one here](https://manage-sandbox.gocardless.com/signup).
Generate an access token and set it as `GOCARDLESS_ACCESS_TOKEN` in your `dev_settings.py`.

## Webhooks

In order to receive GoCardless status webhooks, you need some way of tunneling web
requests so that you can receive them. Currently the easiest way to do this is with
[serveo](https://serveo.net/), which works through SSH - replace `<somename>` with a
unique name for you:

	$ ssh -R <somename>:80:localhost:8000 serveo.net

This will tunnel traffic from `https://<somename>.serveo.net` to your local development
instance. You'll need to add this host to `ALLOWED_HOSTS` in `dev_settings.py`, along
with localhost:

	ALLOWED_HOSTS = ["<somename>.serveo.net", "localhost"]

Now you can configure the GoCardless sandbox webhook (the URL is
`https://<somename>.serveo.net/gocardless-webhook`) and insert the generated secret into
`GOCARDLESS_WEBHOOK_SECRET` in `dev_settings.py`.

At this point, it should hopefully work!

## Bank Details

To set up a GoCardless payment in the sandbox, you'll have to use the [test GoCardless
bank details](https://developer.gocardless.com/getting-started/developer-tools/test-bank-details/).
