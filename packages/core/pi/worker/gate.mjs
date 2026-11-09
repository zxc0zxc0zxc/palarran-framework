/** A serialized HTTP boundary; no provider response or credential enters diagnostics. */
import { randomUUID } from "node:crypto";

export class GateError extends Error {
  constructor(code) {
    super(code);
    this.name = "GateError";
    this.code = code;
  }
}

const MAX_BODY_BYTES = 1024 * 1024;
const MAX_EVENT_BYTES = 128 * 1024;
const integer = (value) => Number.isSafeInteger(value) && value >= 0;

export function validateProfile(profile) {
  if (
    !profile ||
    !["openai-completions", "anthropic-messages"].includes(profile.api) ||
    !["openai", "anthropic"].includes(profile.provider) ||
    (profile.provider === "openai") !==
      (profile.api === "openai-completions") ||
    typeof profile.model !== "string" ||
    !profile.model ||
    profile.model.length > 160 ||
    !integer(profile.max_output_tokens) ||
    profile.max_output_tokens < 1 ||
    profile.max_output_tokens > 128000
  )
    throw new GateError("unsupported_profile");
  let base;
  try {
    base = new URL(profile.base_url);
  } catch {
    throw new GateError("invalid_origin");
  }
  if (
    base.protocol !== "https:" ||
    base.username ||
    base.password ||
    base.search ||
    base.hash
  )
    throw new GateError("invalid_origin");
  const pricing = profile.pricing;
  for (const field of [
    "input_micros_per_million",
    "output_micros_per_million",
  ]) {
    if (!integer(pricing?.[field]) || pricing[field] < 1)
      throw new GateError("pricing_required");
  }
  for (const field of [
    "cache_read_micros_per_million",
    "cache_write_micros_per_million",
  ]) {
    if (pricing[field] !== undefined && !integer(pricing[field]))
      throw new GateError("invalid_pricing");
  }
  return base;
}

function costMicros(usage, pricing, reservation = false) {
  const inputRate = Math.max(
    pricing.input_micros_per_million,
    pricing.cache_write_micros_per_million ?? pricing.input_micros_per_million,
    pricing.cache_read_micros_per_million ?? pricing.input_micros_per_million,
  );
  const terms = reservation
    ? [
        [usage.input_tokens, inputRate],
        [usage.output_tokens, pricing.output_micros_per_million],
      ]
    : [
        [usage.input_tokens, pricing.input_micros_per_million],
        [usage.output_tokens, pricing.output_micros_per_million],
        [
          usage.cache_read_tokens,
          pricing.cache_read_micros_per_million ??
            pricing.input_micros_per_million,
        ],
        [
          usage.cache_write_tokens,
          pricing.cache_write_micros_per_million ??
            pricing.input_micros_per_million,
        ],
      ];
  let value = 0n;
  for (const [tokens, rate] of terms) value += BigInt(tokens) * BigInt(rate);
  const rounded = (value + 999999n) / 1000000n;
  if (rounded > BigInt(Number.MAX_SAFE_INTEGER))
    throw new GateError("cost_overflow");
  return Number(rounded);
}

function textOnly(body) {
  const pending = [body];
  while (pending.length) {
    const value = pending.pop();
    if (Array.isArray(value)) pending.push(...value);
    else if (value && typeof value === "object") {
      if (
        [
          "image",
          "image_url",
          "input_image",
          "input_audio",
          "audio",
          "document",
          "video",
          "file",
        ].includes(value.type)
      )
        throw new GateError("unsupported_multimodal_request");
      pending.push(...Object.values(value));
    }
  }
}

/** Incrementally parse only bounded SSE usage objects, never retaining the transcript. */
function usageParser(api) {
  let pending = "",
    bad = false,
    terminal = false,
    input = null,
    output = null,
    read = 0,
    write = 0;
  const decoder = new TextDecoder();
  function line(value) {
    if (!value.startsWith("data:")) return;
    const data = value.slice(5).trim();
    if (!data) return;
    if (data === "[DONE]") {
      terminal = true;
      return;
    }
    let event;
    try {
      event = JSON.parse(data);
    } catch {
      bad = true;
      return;
    }
    if (api === "openai-completions" && event.usage) {
      const usage = event.usage;
      if (!integer(usage.prompt_tokens) || !integer(usage.completion_tokens)) {
        bad = true;
        return;
      }
      const cached = usage.prompt_tokens_details?.cached_tokens ?? 0;
      if (!integer(cached) || cached > usage.prompt_tokens) {
        bad = true;
        return;
      }
      input = usage.prompt_tokens - cached;
      read = cached;
      output = usage.completion_tokens;
    }
    if (api === "anthropic-messages") {
      if (event.type === "message_stop") terminal = true;
      const usage =
        event.type === "message_start" ? event.message?.usage : event.usage;
      if (!usage) return;
      for (const [key, set] of [
        ["input_tokens", (v) => (input = v)],
        ["output_tokens", (v) => (output = v)],
        ["cache_read_input_tokens", (v) => (read = v)],
        ["cache_creation_input_tokens", (v) => (write = v)],
      ]) {
        if (usage[key] !== undefined) {
          if (!integer(usage[key])) bad = true;
          else set(usage[key]);
        }
      }
    }
  }
  return {
    feed(bytes, final = false) {
      pending += decoder.decode(bytes, { stream: !final });
      if (Buffer.byteLength(pending) > MAX_EVENT_BYTES) {
        bad = true;
        pending = "";
      }
      let end;
      while ((end = pending.indexOf("\n")) >= 0) {
        line(pending.slice(0, end).replace(/\r$/, ""));
        pending = pending.slice(end + 1);
      }
      if (final && pending) {
        line(pending);
        pending = "";
      }
    },
    value() {
      return terminal && !bad && integer(input) && integer(output)
        ? {
            input_tokens: input,
            output_tokens: output,
            cache_read_tokens: read,
            cache_write_tokens: write,
          }
        : null;
    },
  };
}

async function delay(ms, signal) {
  if (signal?.aborted) throw new GateError("request_cancelled");
  await new Promise((resolve, reject) => {
    const timer = setTimeout(done, ms);
    function done() {
      signal?.removeEventListener("abort", cancelled);
      resolve();
    }
    function cancelled() {
      clearTimeout(timer);
      signal?.removeEventListener("abort", cancelled);
      reject(new GateError("request_cancelled"));
    }
    signal?.addEventListener("abort", cancelled, { once: true });
  });
}

/** Injectable callbacks hold the host/run transaction boundary outside a worker. */
export function createGatedFetch({
  profile,
  admit,
  complete,
  transport = globalThis.fetch,
  admission_timeout_ms = 10000,
  now = Date.now,
}) {
  const base = validateProfile(profile);
  if (
    typeof admit !== "function" ||
    typeof complete !== "function" ||
    typeof transport !== "function"
  )
    throw new GateError("broker_required");
  if (
    !integer(admission_timeout_ms) ||
    admission_timeout_ms < 1 ||
    admission_timeout_ms > 60000
  )
    throw new GateError("invalid_admission_timeout");
  const endpoint =
    base.href.replace(/\/$/, "") +
    (profile.api === "openai-completions"
      ? "/chat/completions"
      : "/v1/messages");

  return async function gatedFetch(input, init = {}) {
    const request = input instanceof Request ? input : null;
    let url;
    try {
      url = new URL(request ? request.url : input);
    } catch {
      throw new GateError("invalid_origin");
    }
    const endpointMatch =
      url.href === endpoint ||
      (profile.api === "anthropic-messages" &&
        url.search === "?beta=true" &&
        url.href.slice(0, -url.search.length) === endpoint);
    if (
      !endpointMatch ||
      url.protocol !== "https:" ||
      (init.method ?? request?.method ?? "GET").toUpperCase() !== "POST"
    )
      throw new GateError("request_not_allowed");
    const signal = init.signal ?? request?.signal;
    if (signal?.aborted) throw new GateError("request_cancelled");
    let raw = init.body ?? (request ? await request.clone().text() : null);
    if (raw instanceof Uint8Array) raw = new TextDecoder().decode(raw);
    if (typeof raw !== "string" || Buffer.byteLength(raw) > MAX_BODY_BYTES)
      throw new GateError("invalid_request_body");
    let body;
    try {
      body = JSON.parse(raw);
    } catch {
      throw new GateError("invalid_request_body");
    }
    if (
      !body ||
      typeof body !== "object" ||
      body.model !== profile.model ||
      body.stream !== true
    )
      throw new GateError("request_model_or_transport_changed");
    textOnly(body);
    const capField =
      profile.api === "openai-completions" &&
      body.max_completion_tokens !== undefined
        ? "max_completion_tokens"
        : "max_tokens";
    if (
      !integer(body[capField]) ||
      body[capField] < 1 ||
      body[capField] > profile.max_output_tokens
    )
      throw new GateError("output_cap_required");
    if (
      body.max_tokens !== undefined &&
      body.max_completion_tokens !== undefined
    )
      throw new GateError("ambiguous_output_cap");
    // Request the usage-bearing final chunk rather than treating missing usage as free.
    if (profile.api === "openai-completions")
      body.stream_options = { ...body.stream_options, include_usage: true };
    raw = JSON.stringify(body);
    const inputBound = Buffer.byteLength(raw) + 1024;
    const metadata = {
      request_id: randomUUID(),
      provider: profile.provider,
      model: profile.model,
      input_tokens_bound: inputBound,
      output_tokens_bound: body[capField],
      cost_micros_bound: costMicros(
        { input_tokens: inputBound, output_tokens: body[capField] },
        profile.pricing,
        true,
      ),
    };
    const deadline = now() + admission_timeout_ms;
    while (true) {
      let receipt;
      try {
        receipt = await admit(metadata);
      } catch {
        throw new GateError("admission_unknown");
      }
      if (receipt?.status === "ADMITTED") {
        if (receipt.request_id !== metadata.request_id)
          throw new GateError("admission_identity_mismatch");
        break;
      }
      if (receipt?.status !== "WAIT")
        throw new GateError(
          /^[a-z_]{1,64}$/.test(receipt?.code ?? "")
            ? receipt.code
            : "admission_rejected",
        );
      if (now() >= deadline) throw new GateError("admission_timeout");
      await delay(Math.min(25, Math.max(1, deadline - now())), signal);
    }
    let sealed = false;
    async function settle(outcome, usage = null) {
      if (sealed) return;
      sealed = true;
      if (usage) usage.cost_micros = costMicros(usage, profile.pricing);
      try {
        await complete({ ...metadata, outcome, usage, body_terminal: true });
      } catch {
        throw new GateError("settlement_unknown");
      }
    }
    let response;
    try {
      response = await transport(input, {
        ...init,
        method: "POST",
        body: raw,
        signal,
        redirect: "error",
      });
    } catch {
      await settle("unknown");
      throw new GateError("transport_failed");
    }
    if (response.redirected) {
      await response.body?.cancel();
      await settle("unknown");
      throw new GateError("redirect_rejected");
    }
    if (!response.body) {
      await settle("unknown");
      return response;
    }
    const parser = usageParser(profile.api);
    const reader = response.body.getReader();
    const stream = new ReadableStream(
      {
        async pull(controller) {
          try {
            const value = await reader.read();
            if (value.done) {
              parser.feed(new Uint8Array(), true);
              const usage = response.ok ? parser.value() : null;
              await settle(usage ? "known" : "unknown", usage);
              controller.close();
            } else {
              parser.feed(value.value);
              controller.enqueue(value.value);
            }
          } catch {
            try {
              await settle("unknown");
            } finally {
              controller.error(new GateError("response_stream_failed"));
            }
          }
        },
        async cancel(reason) {
          try {
            await reader.cancel(reason);
          } finally {
            const usage = response.ok ? parser.value() : null;
            await settle(usage ? "known" : "cancelled", usage);
          }
        },
      },
      { highWaterMark: 0 },
    );
    return new Response(stream, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
  };
}
